import os
from pathlib import Path
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

# --- Path Configuration using Python's Pathlib ---
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_RAW_DIR = SCRIPT_DIR.parent / "raw"

# --- 1. The Processing Function (The "Workhorse") ---
def process_pdf_to_pinecone(file_path, index):
    """Handles the extraction, embedding, and uploading of a single PDF."""
    print(f"Reading {file_path.name}...")
    reader = PdfReader(file_path)
    text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])

    if not text.strip():
        print(f"⚠️ Warning: Could not extract text from {file_path.name}. Skipping.")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(text)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    print(f"Uploading {len(chunks)} chunks from {file_path.name}...")
    for i, chunk in enumerate(chunks):
        # Create a unique ID combining filename and index
        unique_id = f"{file_path.stem}_{i}"
        vec = embeddings.embed_query(chunk)
        index.upsert(vectors=[{
            "id": unique_id,
            "values": vec,
            "metadata": {"text": chunk, "source": str(file_path.name)}
        }])

# --- 2. The Orchestrator Function (The "Manager") ---
def run_bulk_ingestion():
    """Finds all PDFs in data/raw and triggers the process."""
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX_NAME")

    # Create Index if needed (Free Tier Specs)
    if index_name not in [idx.name for idx in pc.list_indexes()]:
        print(f"Creating FREE index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    index = pc.Index(index_name)

    # Locate all PDFs using our Python-provided path
    pdf_files = list(DATA_RAW_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"❌ No PDFs found in {DATA_RAW_DIR}. Please add your policy files there.")
        return

    print(f"📂 Found {len(pdf_files)} files. Starting ingestion...")

    for pdf in pdf_files:
        process_pdf_to_pinecone(pdf, index)

    print("✅ All documents processed successfully!")

if __name__ == "__main__":
    run_bulk_ingestion()