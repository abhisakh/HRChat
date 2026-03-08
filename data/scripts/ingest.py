import os
import json
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

# --- Path Configuration ---
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_RAW_DIR = SCRIPT_DIR.parent / "raw"
MANIFEST_FILE = SCRIPT_DIR / "ingest_manifest.json"

def get_file_hash(file_path):
    """Generate a hash to see if the file content changed."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def load_manifest():
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_manifest(manifest):
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=4)

def process_pdf(file_path):
    """Extracts text and splits into chunks."""
    reader = PdfReader(file_path)
    text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    return splitter.split_text(text)

def run_smart_ingestion():
    # 1. Setup Pinecone & Manifest
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX_NAME")
    manifest = load_manifest()

    # Create index if it's your first time
    if index_name not in [idx.name for idx in pc.list_indexes()]:
        pc.create_index(name=index_name, dimension=1536, metric="cosine",
                        spec=ServerlessSpec(cloud="aws", region="us-east-1"))

    index = pc.Index(index_name)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # 2. Scan for PDFs
    pdf_files = list(DATA_RAW_DIR.glob("*.pdf"))
    if not pdf_files:
        print("No PDFs found in data/raw.")
        return

    for pdf_path in pdf_files:
        file_name = pdf_path.name
        current_hash = get_file_hash(pdf_path)

        # Check if we should skip
        if manifest.get(file_name) == current_hash:
            print(f"⏩ Skipping {file_name} (unchanged).")
            continue

        print(f"⚙️ Processing {file_name}...")
        chunks = process_pdf(pdf_path)

        vectors = []
        for i, chunk in enumerate(chunks):
            # Create a deterministic ID: filename_chunkIndex
            chunk_id = f"{pdf_path.stem}_{i}"
            vector_values = embeddings.embed_query(chunk)

            vectors.append({
                "id": chunk_id,
                "values": vector_values,
                "metadata": {"text": chunk, "source": file_name}
            })

            # Upsert in batches of 100
            if len(vectors) == 100:
                index.upsert(vectors=vectors)
                vectors = []

        if vectors:
            index.upsert(vectors=vectors)

        # Update manifest
        manifest[file_name] = current_hash
        save_manifest(manifest)
        print(f"✅ Indexed {file_name}")

if __name__ == "__main__":
    run_smart_ingestion()