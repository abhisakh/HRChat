# HRChat_LLM — Context-Aware HR Chatbot with RBAC

> A multi-user HR assistant powered by **FastAPI**, **LangGraph**, and **Hybrid AI** (SQL + Vector Search).  
> Every user gets a personalised, role-restricted response. No two users see the same data.

---

## 📖 Table of Contents

- [Introduction](#introduction)
- [Why This Project Matters](#why-this-project-matters)
- [How It Works — Architecture Flow](#how-it-works--architecture-flow)
  - [High-Level Flow](#high-level-flow)
  - [Why Each Design Decision Was Made](#why-each-design-decision-was-made)
- [Tech Stack](#tech-stack)
  - [API Layer](#-api-layer)
  - [AI & Agent Orchestration](#-ai--agent-orchestration)
  - [LLM & Embeddings](#-llm--embeddings)
  - [Databases](#-databases)
  - [PDF Ingestion](#-pdf-ingestion)
  - [Security & Auth](#-security--auth)
  - [Data & Dev Tools](#-data--dev-tools)
  - [Frontend (Planned)](#-frontend-planned)
- [Folder Structure](#folder-structure)
- [Backend Deep Dive](#backend-deep-dive)
  - [main.py — The API Gateway](#mainpy--the-api-gateway)
  - [graph.py — The Agent Orchestrator](#graphpy--the-agent-orchestrator)
  - [nodes.py — The Decision Stations](#nodespy--the-decision-stations)
  - [sql_tool.py — The RBAC Enforcer](#sql_toolpy--the-rbac-enforcer)
  - [retriever.py — The Policy Search Engine](#retrieverpy--the-policy-search-engine)
  - [connection.py — The DB Bridge](#connectionpy--the-db-bridge)
- [Data Scripts](#data-scripts)
  - [ingest.py — PDF to Pinecone](#ingestpy--pdf-to-pinecone)
  - [seed_employees.py — Database Seeding](#seed_employeespy--database-seeding)
- [End-to-End Request Flow](#end-to-end-request-flow)
- [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Environment Variables](#environment-variables)
- [Setup and Running Locally](#setup-and-running-locally)
- [File Responsibilities](#file-responsibilities)
- [Security Design](#security-design)
- [Current Limitations](#current-limitations)
- [Future Improvements](#future-improvements)

---

## Introduction

[[Back to Top]](#-table-of-contents)

**HRChat** is a context-aware, multi-user HR assistant that gives every employee instant, personalised answers to HR questions — while making sure they can only ever see data they are authorised to see.

A typical HR department drowns in repetitive queries: *"How many PTO days do I have?"*, *"What is the parental leave policy?"*, *"Who is my supervisor?"*. These questions pull HR staff away from higher-value work, and employees often wait hours or days for answers that should take seconds. HRChat solves this by acting as an always-available, intelligent first point of contact — routing each question to exactly the right data source and returning a natural-language answer in real time.

What makes HRChat different from a simple FAQ bot is its **Hybrid AI architecture**. HR information lives in two very different places:

- **Structured data** — personal records like salary, PTO balance, hire date, and supervisor — stored in a relational database, specific to each individual employee
- **Unstructured data** — company-wide policies, handbooks, and guidelines — stored as PDF documents that don't fit neatly into rows and columns

Most chatbots handle one or the other. HRChat handles both, automatically routing each question to the right source and combining the result into a single coherent answer.

---

## Why This Project Matters

[[Back to Top]](#-table-of-contents)

### The Problem

Traditional HR support has two failure modes:

**Too slow** — employees submit tickets and wait. HR teams spend the majority of their time answering the same handful of questions repeatedly, leaving less time for strategic work like hiring, retention, and culture.

**Too risky** — giving employees direct database access is dangerous. An employee should be able to ask *"What is my salary?"* but must never be able to see a colleague's salary. A simple chatbot with no access control is a security liability.

### What HRChat Demonstrates

| Capability | Why It's Non-Trivial |
|---|---|
| **Hybrid retrieval** | Combines SQL (exact, structured) and vector search (semantic, fuzzy) in a single agent. Most systems use one or the other. |
| **Role-based data isolation** | RBAC is enforced at the SQL query level — not in the UI or the LLM prompt — making it impossible to bypass through prompt injection or request forgery. |
| **Persistent per-user memory** | Each user's conversation history is stored and isolated via LangGraph's `SqliteSaver`. The agent remembers context across sessions. |
| **Agentic routing** | A `router_node` classifies each question and sends it down the correct retrieval path. The LLM only generates the final answer — it does not decide where to look. |
| **Audit trail** | Every question and answer is logged with the data source used, giving organisations full visibility into what was asked and what was returned. |

### Who It's For

- **Employees** — get instant answers to personal HR questions without waiting for a human response
- **HR teams** — reduce repetitive query volume and focus on higher-value work
- **Admins** — full visibility via audit logs and role-management controls
- **Developers** — a working reference implementation of a LangGraph agent with hybrid retrieval, RBAC, and persistent memory

---

## How It Works — Architecture Flow

[[Back to Top]](#-table-of-contents)

### High-Level Flow

```
User sends a message
        ↓
FastAPI (main.py)
  → Verifies credentials (SHA-256 password check)
  → Looks up role from DB — employee / hr / admin
  → Injects role into the LangGraph config
        ↓
LangGraph Agent (graph.py)
  → Carries AgentState through the graph:
    { messages, source_used, context, answer }
        ↓
  router_node (nodes.py)
  → Reads the question
  → Decides: is this about personal data or company policy?
  → Sets state["source_used"] = "sql" OR "vector"
        ↓
  ┌─────────────────────────────────────────────┐
  │  SQL path                  Vector path      │
  │                                             │
  │  sql_node (nodes.py)       retrieve_node    │
  │  → reads user_id + role    (nodes.py)       │
  │    from LangGraph config   → runs semantic  │
  │  → calls sql_tool.py         search on      │
  │  → RBAC enforced at query    Pinecone       │
  │    level (salary hidden,   → returns top-3  │
  │    WHERE user_id = ?)        policy chunks  │
  └─────────────────────────────────────────────┘
        ↓
  generate_node (nodes.py)
  → Receives context (SQL result OR policy chunks)
  → Calls OpenAI LLM: "Answer this question using the context"
  → Writes natural-language answer to state["answer"]
        ↓
  audit_node (nodes.py)
  → Calls save_to_audit_log()
  → Saves user_id, question, answer, source_used to chat_audit_logs
        ↓
FastAPI returns JSON to the client:
  { "user_id": ..., "answer": ..., "source": "sql" | "vector" }
```

---

### Why Each Design Decision Was Made

**Why LangGraph instead of a simple LangChain chain?**

A linear chain cannot branch. HRChat needs to route questions to different tools based on intent — that requires a graph with conditional edges. LangGraph's `StateGraph` also provides built-in checkpointing via `SqliteSaver`, giving the agent persistent memory across sessions with zero extra code.

**Why is the router a separate node and not part of the LLM prompt?**

Keeping routing logic explicit and deterministic means the system is predictable and auditable. If the LLM were responsible for choosing tools via function calling, a cleverly worded prompt could manipulate it into using the wrong tool. A dedicated `router_node` makes the decision based on pattern matching — not LLM judgment.

**Why is RBAC enforced in `sql_tool.py` and not in the API layer?**

The API layer (`main.py`) is the right place to authenticate — it verifies who you are. But authorisation — what you're allowed to see — must happen as close to the data as possible. If RBAC were only in the API, a bug in the agent or a compromised node could bypass it. By enforcing it inside `sql_tool.py` at the SQL query level, access control survives even if everything above it misbehaves.

**Why Hybrid retrieval (SQL + Vector) instead of one or the other?**

SQL is perfect for exact, structured lookups: *"What is my PTO balance?"* has a precise answer in a specific row and column. Vector search is perfect for semantic, fuzzy lookups: *"What is the policy on working from home?"* requires finding the right paragraph from a PDF. Neither tool alone handles both question types well — combining them gives the agent the right instrument for every question.

**Why SQLite instead of PostgreSQL?**

SQLite is file-based and requires zero infrastructure setup, making it ideal for development and local testing. The schema and queries are identical to PostgreSQL, so migrating to a production database requires only changing the connection string.

---

## Tech Stack

[[Back to Top]](#-table-of-contents)

HRChat is built entirely in Python on the backend, with each technology chosen for a specific reason — not just familiarity.

---

### 🌐 API Layer

| Package | Version | Role |
|---|---|---|
| `fastapi` | Latest | Web framework — handles all HTTP endpoints, request validation, and startup events |
| `uvicorn` | Latest | ASGI server that runs the FastAPI app |
| `pydantic` | v2+ | Request/response model validation (`LoginRequest`, `ChatRequest`, `ChatResponse`, etc.) |

**Why FastAPI?** It gives automatic `/docs` Swagger UI, async support, and Pydantic validation out of the box — meaning every endpoint is self-documenting and type-safe with minimal boilerplate.

---

### 🤖 AI & Agent Orchestration

| Package | Version | Role |
|---|---|---|
| `langgraph` | Latest | `StateGraph` that defines the agent's execution flow — nodes, conditional edges, and memory |
| `langchain-openai` | Latest | OpenAI LLM wrapper (`ChatOpenAI`) used by `generate_node` to write final answers |
| `langchain-pinecone` | Latest | `PineconeVectorStore` used by `retriever.py` to query ingested policy embeddings |
| `langchain-text-splitters` | Latest | `RecursiveCharacterTextSplitter` used by `ingest.py` to chunk PDF text |

**Why LangGraph over a plain LangChain chain?** A linear chain cannot branch. HRChat needs to route questions to different tools depending on intent — that requires a graph with conditional edges. LangGraph also provides `SqliteSaver` for persistent per-user memory at zero extra cost.

---

### 🧠 LLM & Embeddings

| Model | Provider | Used In | Purpose |
|---|---|---|---|
| `gpt-4o-mini` / `gpt-4` | OpenAI | `generate_node` | Writes natural-language answers from retrieved context |
| `text-embedding-3-small` | OpenAI | `ingest.py` + `retriever.py` | Converts PDF chunks and user queries into 1536-dim vectors for semantic search |

**Why `text-embedding-3-small`?** It produces 1536-dimensional embeddings at a fraction of the cost of `text-embedding-ada-002`, while matching or exceeding its retrieval performance on most benchmarks.

---

### 🗃️ Databases

| Database | File | Role |
|---|---|---|
| SQLite | `hr_database.db` | Stores `employees`, `users`, and `chat_audit_logs` tables — the core relational data |
| SQLite | `checkpoints.sqlite` | Stores LangGraph conversation checkpoints via `SqliteSaver` — enables per-user persistent memory |
| Pinecone | Cloud index | Stores 1536-dim embeddings of HR policy PDF chunks — enables semantic vector search |

**Why SQLite for development?** It is file-based — zero infrastructure, zero configuration. The SQL schema and queries are compatible with PostgreSQL, so upgrading for production is a connection string change.

**Why two separate SQLite files?** `hr_database.db` is business data — employee records, credentials, audit logs. `checkpoints.sqlite` is agent state — LangGraph conversation memory. Keeping them separate means the agent's memory layer can be wiped or swapped without touching business data.

---

### 📄 PDF Ingestion

| Package | Role |
|---|---|
| `pypdf` | Extracts raw text from each page of uploaded HR policy PDFs |
| `langchain-text-splitters` | Splits extracted text into overlapping chunks (`chunk_size=1000`, `chunk_overlap=100`) |
| `pinecone` | Python client — creates the index and upserts vector batches of 100 |
| `python-dotenv` | Loads `OPENAI_API_KEY` and `PINECONE_API_KEY` from `.env` during ingestion |
| `hashlib` (stdlib) | MD5 hashes each PDF to detect changes — unchanged files are skipped on re-runs |

---

### 🔐 Security & Auth

| Tool | Role |
|---|---|
| `hashlib.sha256` (stdlib) | Hashes passwords before storing in the `users` table — plaintext is never written to disk |
| `sqlite3` (stdlib) | Direct DB access with `PRAGMA foreign_keys = ON` — enforces referential integrity |
| Role `CHECK` constraint | SQLite-level enforcement: only `'employee'`, `'hr'`, `'admin'` are valid role values |

> ⚠️ **Known limitation:** SHA-256 is a fast hashing algorithm. Production deployments should replace it with `bcrypt` or `argon2`, which are specifically designed for password hashing and are resistant to brute-force attacks.

---

### 🌱 Data & Dev Tools

| Package | Role |
|---|---|
| `faker` | Generates realistic fake employee data (names, emails, phone numbers, hire dates) for seeding |
| `random` (stdlib) | Picks random positions, departments, locations, and roles in auto-seed mode |

---

### 🖥️ Frontend *(Planned)*

| Technology | Role |
|---|---|
| Next.js 15+ | React framework with App Router for the chat UI |
| Shadcn/UI | Component library — buttons, inputs, cards, chat bubbles |
| Axios / Fetch API | HTTP client consuming the FastAPI backend |
| `useChat` hook | Custom hook for managing chat state and streaming |

---

### Full Dependency Map

```
User Request
    │
    ▼
fastapi + uvicorn + pydantic          ← API layer
    │
    ▼
langgraph (StateGraph)                ← Agent orchestration
    │         │
    │    SqliteSaver                  ← checkpoints.sqlite (memory)
    │
    ├── router_node
    │       │
    │   ┌───┴───────────────────┐
    │   ▼                       ▼
    │ sql_node              retrieve_node
    │ sqlite3 stdlib         langchain-pinecone
    │ hr_database.db         Pinecone cloud index
    │   └───────────┬───────────┘
    │               ▼
    │         generate_node
    │         langchain-openai (ChatOpenAI)
    │               │
    │         audit_node
    │         sqlite3 → chat_audit_logs
    ▼
JSON response
```

---

## Folder Structure

[[Back to Top]](#-table-of-contents)

```
HRChat/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── graph.py            # LangGraph StateGraph — nodes, edges, memory
│   │   │   ├── state.py            # AgentState TypedDict definition
│   │   │   ├── nodes.py            # router_node, sql_node, retrieve_node,
│   │   │   │                       # generate_node, audit_node
│   │   │   └── tools/
│   │   │       ├── retriever.py    # Pinecone vector retriever (top-k=3)
│   │   │       └── sql_tool.py     # 🔐 RBAC enforcement + SQLite queries
│   │   └── db/
│   │       ├── schemas/
│   │       │   ├── employees.sql   # Employee table blueprint
│   │       │   ├── auth.sql        # Users + roles table blueprint
│   │       │   └── audit_logs.sql  # Chat audit log table blueprint
│   │       ├── connection.py       # init_db(), save_to_audit_log()
│   │       ├── hr_database.db      # SQLite DB (auto-created on startup)
│   │       └── checkpoints.sqlite  # LangGraph memory (auto-created)
│   └── main.py                     # FastAPI app — all endpoints live here
│
├── frontend/                       # Next.js / React (planned)
│   ├── app/
│   ├── components/
│   │   ├── chat/                   # ChatWindow, MessageBubble
│   │   └── ui/                     # Buttons, Inputs, Cards (Shadcn/UI)
│   ├── hooks/                      # useChat, useLangGraphStreaming
│   └── lib/                        # Axios / Fetch API client
│
├── data/
│   ├── raw/
│   │   └── *.pdf                   # Drop HR policy PDFs here for ingestion
│   └── scripts/
│       ├── ingest.py               # PDF → chunk → embed → Pinecone upsert
│       ├── seed_employees.py       # Seed fake or manual employees into SQLite
│       └── ingest_manifest.json    # Tracks which PDFs are already indexed
│
├── .env                            # API keys (never commit this)
├── requirements.txt
└── docker-compose.yml
```

---

## Backend Deep Dive

[[Back to Top]](#-table-of-contents)

### `main.py` — The API Gateway

[[Back to Top]](#-table-of-contents)

The only file that communicates with the outside world. Hosts all HTTP endpoints and two critical internal helpers.

**On startup**, calls `init_db()` to ensure all SQLite tables exist before any request arrives:

```python
@app.on_event("startup")
async def startup_event():
    init_db()
```

**Key internal helpers:**

```python
def verify_user(username, password):
    # SHA-256 hashes the password and checks against the users table
    # Returns: { "user_id": ..., "role": ... }  or  None

def get_user_role(user_id):
    # Fetches role from DB for a given user_id
    # Returns: "employee" | "hr" | "admin"  (defaults to "employee" if not found)
```

**The chat flow — role is always server-side:**

```python
# 1. Look up the user's role from the DB (never trusted from the request body)
user_role = get_user_role(request.user_id)

# 2. Inject role into LangGraph config
config = {
    "configurable": {
        "thread_id": request.user_id,   # Isolates each user's conversation memory
        "role": user_role               # Passed into every node in the graph
    }
}

# 3. Run the agent
final_state = hr_agent.invoke(initial_state, config=config)
```

> `thread_id = user_id` means User A's conversation history is completely isolated from User B's — even if they ask the same questions.

---

### `graph.py` — The Agent Orchestrator

[[Back to Top]](#-table-of-contents)

Defines the **LangGraph `StateGraph`** — the execution flowchart of the entire agent.

**Node registration:**

```python
builder.add_node("router",     router_node)
builder.add_node("retrieve",   retrieve_node)
builder.add_node("sql_search", sql_node)
builder.add_node("generate",   generate_node)
builder.add_node("audit",      audit_node)
```

**Conditional routing** — reads `state["source_used"]` after the router runs:

```python
builder.add_conditional_edges(
    "router",
    lambda state: state["source_used"],
    {
        "sql":    "sql_search",   # Personal data question → SQL tool
        "vector": "retrieve"      # Policy question → Pinecone
    }
)
```

**Full execution path:**

```
START → router → [sql_search  OR  retrieve] → generate → audit → END
```

Both SQL and vector paths converge at `generate`, so the response format is always consistent.

**Persistent memory** via `SqliteSaver` — conversations survive server restarts:

```python
conn   = sqlite3.connect("backend/app/db/checkpoints.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)
hr_agent = builder.compile(checkpointer=memory)
```

---

### `nodes.py` — The Decision Stations

[[Back to Top]](#-table-of-contents)

Each node is a Python function that reads from and writes to the shared `AgentState` dictionary.

| Node | Reads from state | What it does | Writes to state |
|---|---|---|---|
| `router_node` | `messages` | Classifies question: SQL or vector? | `source_used` |
| `sql_node` | `messages`, config (`user_id`, `role`) | Calls `query_employee_db()` | `context` |
| `retrieve_node` | `messages` | Runs Pinecone semantic search (top-3 chunks) | `context` |
| `generate_node` | `context`, `messages` | Calls LLM with context, writes final answer | `answer` |
| `audit_node` | `user_id`, question, `answer`, `source_used` | Writes row to `chat_audit_logs` | — |

---

### `sql_tool.py` — The RBAC Enforcer

[[Back to Top]](#-table-of-contents)

> 🔐 **This is the most critical security file in the system.**

`query_employee_db(user_id, role, user_question)` enforces data access at the SQL query level. The role determines which query runs — there is no way to bypass it from the UI or the LLM.

**Employee** — sees only their own record, salary column excluded:

```python
query = """
    SELECT first_name, last_name, position, department,
           available_pto, hire_date, supervisor, location, skills
    FROM employees
    WHERE user_id = ?
"""
# salary is intentionally omitted from the SELECT
```

**HR** — full read access to all employees:

```python
query = "SELECT * FROM employees"
cursor.execute(query)
rows = cursor.fetchall()
return f"HR View: Retrieved {len(rows)} employee records."
```

**Admin** — same read access as HR, plus `/delete_user` endpoint privilege.

**Invalid role:**

```python
return "Access denied: Invalid role."
```

The DB path is resolved relative to the file, so it works from any working directory:

```python
DB_PATH = Path(__file__).parent.parent.parent / "db" / "hr_database.db"
```

---

### `retriever.py` — The Policy Search Engine

[[Back to Top]](#-table-of-contents)

Connects to the Pinecone index created by `ingest.py` and wraps it as a LangChain retriever.

```python
def get_retriever():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectorstore = PineconeVectorStore(
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        embedding=embeddings,
        text_key="text"       # Must match the metadata key written in ingest.py
    )

    return vectorstore.as_retriever(search_kwargs={"k": 3})
    #                                                 ↑
    #                               returns top 3 most relevant policy chunks
```

The retriever finds the 3 most semantically relevant chunks from ingested PDFs and passes them as context to `generate_node`.

---

### `connection.py` — The DB Bridge

[[Back to Top]](#-table-of-contents)

Two responsibilities:

**`init_db()`** — called on FastAPI startup and by `seed_employees.py`. Reads all `.sql` blueprint files from `/schemas/` and executes them against `hr_database.db`, creating all tables if they don't already exist.

**`save_to_audit_log()`** — called by `audit_node` after every response. Writes `user_id`, `question`, `answer`, and `source` to the `chat_audit_logs` table.

---

## Data Scripts

[[Back to Top]](#-table-of-contents)

### `ingest.py` — PDF to Pinecone

[[Back to Top]](#-table-of-contents)

Scans `data/raw/` for PDF files and uploads them to Pinecone as vector embeddings. Uses an MD5 manifest to skip files that haven't changed since the last run.

**Smart ingestion check:**

```python
current_hash = get_file_hash(pdf_path)

if manifest.get(file_name) == current_hash:
    print(f"⏩ Skipping {file_name} (unchanged).")
    continue
```

**Processing pipeline per PDF:**

```
PDF file
  → PdfReader extracts raw text from all pages
  → RecursiveCharacterTextSplitter chunks it
     (chunk_size=1000, chunk_overlap=100)
  → OpenAI embeds each chunk  (text-embedding-3-small, 1536 dims)
  → Pinecone upserts in batches of 100
  → Manifest updated with new MD5 hash
```

**Vector record format written to Pinecone:**

```python
{
    "id":     "umbrella_corp_policies_42",    # {filename_stem}_{chunkIndex}
    "values": [...],                           # 1536-dim embedding vector
    "metadata": {
        "text":   "...chunk content...",       # text_key="text" in retriever.py
        "source": "umbrella_corp_policies.pdf"
    }
}
```

To add new policy documents: drop any `.pdf` into `data/raw/` and re-run `ingest.py`. Already-indexed, unchanged files are skipped automatically.

---

### `seed_employees.py` — Database Seeding

[[Back to Top]](#-table-of-contents)

Populates `hr_database.db` with fake or manually entered employees and their login credentials. The script evolved through three versions (basic seeding → password support → RBAC support) — the active version supports both auto and manual modes.

**Two modes:**

| Mode | How it works | Best for |
|---|---|---|
| **Auto** (default) | `Faker` generates all fields randomly | Quick dev setup |
| **Manual** | Interactive CLI prompts each field with sensible defaults | Creating specific test users |

**What gets written per employee:**

```python
# employees table
(user_id, first_name, last_name, email, phone_number,
 position, department, skills, location, hire_date, supervisor, salary)

# users table
(user_id, username, password_hash, role)
```

**Role in auto mode:** randomly assigned from `["employee", "hr", "admin"]` for testing coverage.

**Role in `/register` endpoint:** derived from position — any position containing `"hr"` gets role `"hr"`, otherwise `"employee"`. Users cannot self-select.

**Default password for all seeded users:** `password123` (SHA-256 hashed before storage).

**Running the script:**

```bash
cd data/scripts
python seed_employees.py
# Seed manually? (yes/no, default: no): no
# Number of employees to seed (default: 5): 20
```

---

## End-to-End Request Flow

[[Back to Top]](#-table-of-contents)

Complete trace for an employee asking *"How many vacation days do I have?"*:

```
1.  POST /chat
    Body: { "user_id": "user_4821", "message": "How many vacation days do I have?" }

2.  main.py
    → get_user_role("user_4821")  →  returns "employee"
    → config = { thread_id: "user_4821", role: "employee" }
    → hr_agent.invoke({ messages: [HumanMessage(...)] }, config)

3.  graph.py — LangGraph begins execution at START
    → router_node reads the message
    → Classifies as a personal data question
    → Sets state["source_used"] = "sql"
    → Conditional edge routes to → sql_search

4.  sql_node (nodes.py)
    → Reads user_id and role from LangGraph config
    → Calls query_employee_db("user_4821", "employee", "How many vacation days...")

5.  sql_tool.py — RBAC enforced at query level
    → role == "employee"  →  runs restricted SELECT (no salary column)
    → WHERE user_id = "user_4821"  →  only their own row is returned
    → Formats and returns: "Your Employee Record: ... Available PTO: 12 days ..."

6.  generate_node (nodes.py)
    → Receives SQL result as context
    → Calls LLM: "Based on this data, answer the question naturally"
    → LLM writes: "You currently have 12 vacation days available."
    → Sets state["answer"]

7.  audit_node (nodes.py)
    → Calls save_to_audit_log()
    → Saves: user_id="user_4821", question, answer, source="sql"

8.  FastAPI returns JSON:
    {
      "user_id": "user_4821",
      "answer":  "You currently have 12 vacation days available.",
      "source":  "sql"
    }
```

---

## Role-Based Access Control (RBAC)

[[Back to Top]](#-table-of-contents)

> **Design principle:** RBAC is enforced at the **data access layer** (`sql_tool.py`). Even if a client sends a forged `user_id`, the SQL query itself restricts what data is returned. The UI and LLM have no ability to override this.

### The Three Roles

| Role | Data Access | Admin Actions |
|---|---|---|
| `employee` | Own record only. Salary **always excluded**. | None |
| `hr` | All employee records (`SELECT * FROM employees`) | None |
| `admin` | All employee records + `/delete_user` endpoint | Delete any user and their data |

### How Role Is Determined

**At registration (`/register`):**

```python
if "hr" in request.position.lower():
    role = "hr"
else:
    role = "employee"
```

Role is derived server-side from job position. Users cannot choose their own role.

**At login (`/login`):**

```python
# Role is fetched from DB and returned in the response
{ "user_id": "user_4821", "role": "employee", "status": "success" }
```

**At every chat request (`/chat`):**

```python
user_role = get_user_role(request.user_id)  # Always re-fetched from DB
# Role from the request body is never used
```

### What Each Role Sees

**Employee asks "What is my salary?"**

```
Your Employee Record:
- Name: John Doe
- Position: Software Engineer
- Available PTO: 12 days
- Hire Date: 2022-03-15
- Supervisor: Jane Smith
- Location: Raccoon City HQ
- Skills: Python, Security
(Salary information is restricted.)
```

**HR asks "Show me all employees"**

```
HR View: Retrieved 47 employee records.
```

**Unknown or invalid role:**

```
Access denied: Invalid role.
```

---

## API Reference

[[Back to Top]](#-table-of-contents)

All endpoints are served at `http://localhost:8000`. Interactive Swagger docs available at `/docs`.

### `POST /login`

Authenticate a user and retrieve their `user_id` and `role`.

**Request body:**
```json
{
  "username": "john",
  "password": "password123"
}
```

**Success response:**
```json
{
  "user_id": "user_4821",
  "role": "employee",
  "status": "success"
}
```

Returns `401` if credentials are invalid.

---

### `POST /register`

Register a new employee. Role is auto-assigned from the position field.

**Request body:**
```json
{
  "username":   "jane_doe",
  "password":   "securepass",
  "first_name": "Jane",
  "last_name":  "Doe",
  "position":   "HR Specialist",
  "salary":     75000.00
}
```

**Success response:**
```json
{
  "status":  "success",
  "user_id": "user_3847",
  "role":    "hr"
}
```

Returns `400` if username is already taken. Runs as a transaction — rolls back on any failure.

---

### `POST /chat`

Send a message to the HR agent. Role is always fetched server-side.

**Request body:**
```json
{
  "user_id": "user_4821",
  "message": "How many vacation days do I have?"
}
```

**Success response:**
```json
{
  "user_id": "user_4821",
  "answer":  "You currently have 12 vacation days available.",
  "source":  "sql"
}
```

`source` is `"sql"` for personal data questions, `"vector"` for policy questions.

---

### `POST /delete_user`

Delete a user and all their associated records. **Admin role required.**

**Request body:**
```json
{
  "user_id": "user_3847"
}
```

**Success response:**
```json
{
  "status":  "success",
  "message": "User user_3847 deleted"
}
```

Deletes from `users`, `employees`, and `chat_audit_logs` in a single transaction with rollback on failure. Returns `403` if requester is not admin, `404` if user not found.

---

### `GET /health`

```json
{ "status": "online" }
```

---

## Database Schema

[[Back to Top]](#-table-of-contents)

Three SQLite tables defined as `.sql` blueprints in `backend/app/db/schemas/`. All are created via `init_db()` on startup using `CREATE TABLE IF NOT EXISTS`, so they are safe to run repeatedly.

### `employees` table (`employees.sql`)

This is the **primary data table** — created first because `users` holds a foreign key to it.

```sql
CREATE TABLE IF NOT EXISTS employees (
    user_id      TEXT     PRIMARY KEY,
    first_name   TEXT,
    last_name    TEXT,
    email        TEXT,
    phone_number TEXT,
    position     TEXT,
    department   TEXT,
    skills       TEXT,              -- Stored as a comma-separated string
    location     TEXT,
    hire_date    DATE,
    supervisor   TEXT,
    salary       REAL,
    available_pto INTEGER DEFAULT 15  -- Default 15 days PTO on creation
);
```

| Column | Type | Constraint | Notes |
|---|---|---|---|
| `user_id` | TEXT | PRIMARY KEY | Format: `user_4821`. Maps to `employee_id` conceptually. |
| `first_name` | TEXT | — | |
| `last_name` | TEXT | — | |
| `email` | TEXT | — | |
| `phone_number` | TEXT | — | |
| `position` | TEXT | — | Used by `/register` to derive role (`"hr"` in position → role `hr`) |
| `department` | TEXT | — | e.g. IT, HR, Security |
| `skills` | TEXT | — | Comma-separated string, e.g. `"Python, Security"` |
| `location` | TEXT | — | e.g. Raccoon City HQ, Umbrella Europe |
| `hire_date` | DATE | — | Format: `YYYY-MM-DD` |
| `supervisor` | TEXT | — | |
| `salary` | REAL | — | ⚠️ Excluded from `SELECT` for `employee` role in `sql_tool.py` |
| `available_pto` | INTEGER | DEFAULT 15 | Days of PTO remaining |

---

### `users` table (`auth.sql`)

Stores login credentials and roles. Has a **foreign key constraint** back to `employees`, so an employee record must exist before a user record can be created.

```sql
CREATE TABLE IF NOT EXISTS users (
    user_id       TEXT     PRIMARY KEY,
    username      TEXT     UNIQUE NOT NULL,
    password_hash TEXT     NOT NULL,
    role          TEXT     NOT NULL DEFAULT 'employee'
                           CHECK(role IN ('employee', 'hr', 'admin')),
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES employees(user_id)
);
```

| Column | Type | Constraint | Notes |
|---|---|---|---|
| `user_id` | TEXT | PRIMARY KEY, FK → `employees(user_id)` | Shared key — links auth record to employee record |
| `username` | TEXT | UNIQUE, NOT NULL | Login handle |
| `password_hash` | TEXT | NOT NULL | SHA-256 hash — plaintext is never stored |
| `role` | TEXT | NOT NULL, DEFAULT `'employee'`, CHECK constraint | Only `'employee'`, `'hr'`, or `'admin'` are accepted — enforced at DB level |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Account creation timestamp |

> **Note:** The `CHECK(role IN ('employee', 'hr', 'admin'))` constraint means invalid roles are rejected by SQLite itself — not just by application logic.

---

### `chat_audit_logs` table (`chat_audit_logs.sql`)

An append-only log of every question asked and every answer returned. Written by `audit_node` via `save_to_audit_log()` after every chat response.

```sql
CREATE TABLE IF NOT EXISTS chat_audit_logs (
    id          INTEGER  PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT,
    question    TEXT,
    answer      TEXT,
    source_used TEXT,
    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Type | Constraint | Notes |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique log entry ID |
| `user_id` | TEXT | — | Who asked the question |
| `question` | TEXT | — | Raw user message |
| `answer` | TEXT | — | LLM-generated response |
| `source_used` | TEXT | — | `"sql"` or `"vector"` — matches `state["source_used"]` in the graph |
| `timestamp` | DATETIME | DEFAULT CURRENT_TIMESTAMP | When the interaction occurred |

> **Note:** The column is named `source_used` (not `source`) — this matches the field name in `AgentState` and the value set by `router_node` in `nodes.py`.

---

### Schema Relationships

```
employees (user_id)  ←──── users (user_id)   [FK, enforced by PRAGMA foreign_keys = ON]
employees (user_id)  ←──── chat_audit_logs (user_id)   [soft reference, no FK constraint]
```

Creation order matters: `employees` must be initialised before `users` due to the foreign key dependency.

---

## Environment Variables

[[Back to Top]](#-table-of-contents)

Create a `.env` file in the project root:

```env
# OpenAI — used by retriever.py and generate_node
OPENAI_API_KEY=sk-...

# Pinecone — used by ingest.py and retriever.py
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=hrchat-policies
```

`ingest.py` loads these via `python-dotenv`. All other files read them from the OS environment (set by FastAPI / Uvicorn at startup).

---

## Setup and Running Locally

[[Back to Top]](#-table-of-contents)

### Prerequisites

Make sure the following are installed before you begin:

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | Check with `python --version` |
| pip | Latest | Check with `pip --version` |
| Git | Any | For cloning the repo |
| OpenAI API Key | — | Required for LLM + embeddings |
| Pinecone Account | — | Required for vector search |

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/abhisakh/HRChat.git
cd HRChat
```

---

### Step 2 — Create a Virtual Environment

```bash
# Create the environment
python -m venv venv

# Activate it — macOS / Linux
source venv/bin/activate

# Activate it — Windows
venv\Scripts\activate
```

You should see `(venv)` at the start of your terminal prompt once activated.

---

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

Key packages that will be installed:

| Package | Purpose |
|---|---|
| `fastapi` | API framework |
| `uvicorn` | ASGI server to run FastAPI |
| `langgraph` | Agent orchestration (StateGraph) |
| `langchain-openai` | LLM + embeddings via OpenAI |
| `langchain-pinecone` | Pinecone vector store integration |
| `pinecone` | Pinecone client |
| `pypdf` | PDF text extraction |
| `faker` | Fake employee data generation |
| `python-dotenv` | `.env` file loading |
| `pydantic` | Request/response validation |

---

### Step 4 — Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Then open `.env` and fill in your keys:

```env
# OpenAI — used for LLM responses and text embeddings
OPENAI_API_KEY=sk-...

# Pinecone — used for storing and searching HR policy documents
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=hrchat-policies
```

> ⚠️ Never commit `.env` to version control. It is already listed in `.gitignore`.

---

### Step 5 — Ingest Policy Documents into Pinecone

Drop your HR policy PDF files into `data/raw/`, then run:

```bash
python data/scripts/ingest.py
```

Expected output:

```
⚙️  Processing umbrella_corp_policies.pdf...
✅ Indexed umbrella_corp_policies.pdf
```

Already-indexed, unchanged files are skipped automatically on subsequent runs thanks to the MD5 manifest. To re-index a file, delete its entry from `data/scripts/ingest_manifest.json`.

---

### Step 6 — Seed the Database

Populate `hr_database.db` with employee records and login credentials:

```bash
python data/scripts/seed_employees.py
```

Follow the prompts:

```
Seed manually? (yes/no, default: no): no
Number of employees to seed (default: 5): 20

🏗️  Building database schemas from SQL files...
🌱 Seeding 20 employees with credentials and roles...
Seeded user: alice (ID: user_4821) with role: employee
Seeded user: james (ID: user_3047) with role: hr
...
✅ Seeding complete.
```

> All seeded users have the default password `password123`.

To add a specific test user interactively:

```bash
python data/scripts/seed_employees.py
# Seed manually? (yes/no, default: no): yes
# Number of employees to seed (default: 5): 1
# --- Enter employee details ---
# First Name: John
# Last Name: Doe
# Username: john_doe
# ...
```

---

### Step 7 — Start the Backend with Uvicorn

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

| Flag | What it does |
|---|---|
| `backend.main:app` | Points Uvicorn to the `app` object inside `backend/main.py` |
| `--reload` | Auto-restarts the server on code changes (development only, remove in production) |
| `--host 0.0.0.0` | Makes the server accessible on your local network, not just `localhost` |
| `--port 8000` | Serves on port 8000 |

Expected startup output:

```
Initializing HR Databases...
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

The two SQLite files are auto-created on first startup:
- `hr_database.db` — created by `init_db()` via `connection.py`
- `checkpoints.sqlite` — created by LangGraph `SqliteSaver` on the first `/chat` call

---

### Step 8 — Verify Everything Is Running

**Health check:**

```bash
curl http://localhost:8000/health
# {"status":"online"}
```

**Login:**

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}'

# {"user_id": "user_4821", "role": "employee", "status": "success"}
```

**Chat:**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_4821", "message": "How many vacation days do I have?"}'

# {"user_id": "user_4821", "answer": "You currently have 15 vacation days available.", "source": "sql"}
```

Or open **`http://localhost:8000/docs`** in your browser for the full interactive Swagger UI.

---

### Folder State After Full Setup

After completing all steps, your `backend/app/db/` folder will contain:

```
db/
├── schemas/
│   ├── employees.sql
│   ├── auth.sql
│   └── audit_logs.sql
├── connection.py
├── hr_database.db        ← created by init_db() on first startup
└── checkpoints.sqlite    ← created by LangGraph SqliteSaver on first /chat
```

---

### Common Issues

| Problem | Likely Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: backend` | Running from wrong directory | Run all commands from the project root (`HRChat/`) |
| `sqlite3.OperationalError: no such table` | DB not initialised | Run `seed_employees.py` or start the server (calls `init_db()` on startup) |
| `pinecone.exceptions.NotFoundException` | Index name mismatch | Check `PINECONE_INDEX_NAME` in `.env` matches your Pinecone dashboard |
| `openai.AuthenticationError` | Invalid API key | Double-check `OPENAI_API_KEY` in `.env` |
| `Port 8000 already in use` | Another process on that port | Use `--port 8001` or kill the existing process |

---

## File Responsibilities

[[Back to Top]](#-table-of-contents)

| File | Location | Responsibility |
|---|---|---|
| `main.py` | `backend/` | All HTTP endpoints, DB helpers, startup event |
| `graph.py` | `agent/` | `StateGraph` definition — nodes, edges, `SqliteSaver` memory |
| `state.py` | `agent/` | `AgentState` TypedDict shared across all nodes |
| `nodes.py` | `agent/` | `router_node`, `sql_node`, `retrieve_node`, `generate_node`, `audit_node` |
| `sql_tool.py` | `agent/tools/` | 🔐 RBAC enforcement + all SQLite employee queries |
| `retriever.py` | `agent/tools/` | Pinecone vector store connection, returns top-3 chunks |
| `connection.py` | `db/` | `init_db()` schema setup + `save_to_audit_log()` |
| `employees.sql` | `db/schemas/` | `employees` table DDL |
| `auth.sql` | `db/schemas/` | `users` table DDL |
| `audit_logs.sql` | `db/schemas/` | `chat_audit_logs` table DDL |
| `ingest.py` | `data/scripts/` | Smart PDF ingestion with MD5 manifest, batched Pinecone upsert |
| `seed_employees.py` | `data/scripts/` | Auto + manual employee seeding with full RBAC support |

---

## Security Design

[[Back to Top]](#-table-of-contents)

| Layer | What it does | File |
|---|---|---|
| **API** | Password SHA-256 hashed before any DB write | `main.py` |
| **API** | Role re-fetched from DB on every `/chat` — never trusted from client | `main.py` |
| **API** | Role derived from job position at registration — users cannot self-assign | `main.py` |
| **API** | `/delete_user` verifies requester role before executing | `main.py` |
| **API** | All destructive operations wrapped in transactions with rollback | `main.py` |
| **Agent** | Role injected into LangGraph config, propagated to every node | `graph.py` |
| **Data Layer** | SQL query changes based on role — salary excluded for employees | `sql_tool.py` ✅ |
| **Data Layer** | Employee query always `WHERE user_id = ?` — cross-user access impossible | `sql_tool.py` ✅ |
| **DB** | Foreign keys enforced via `PRAGMA foreign_keys = ON` | `connection.py` |
| **Memory** | `thread_id = user_id` — conversation history is per-user isolated | `graph.py` |

---

## Current Limitations

[[Back to Top]](#-table-of-contents)

- **No JWT** — `user_id` is passed in the request body. The SQL layer still restricts data by role, but a client could attempt to send any `user_id` string.
- **SHA-256 password hashing** — SHA-256 is fast, making brute-force attacks cheaper. Production should use `bcrypt` or `argon2`.
- **Static SQL queries** — `sql_tool.py` runs pre-written queries. It does not yet dynamically interpret natural language into SQL.
- **HR and Admin read access are identical** — both run `SELECT * FROM employees`. Admin's extra privilege is only the `/delete_user` endpoint.
- **No logout / token invalidation** — there is no session or token mechanism to invalidate yet.
- **`user_id` collision risk** — IDs are `user_{random 4-digit number}`. With many users, ID collisions become likely. UUIDs should replace this pattern.

---

## Future Improvements

[[Back to Top]](#-table-of-contents)

| Priority | Improvement | Detail |
|---|---|---|
| 🔴 High | **JWT Authentication** | Signed tokens replace raw `user_id` in requests. Role lives inside the token — no DB lookup needed per request. |
| 🔴 High | **bcrypt / Argon2 hashing** | Replace SHA-256 with a slow, salted algorithm designed for passwords. |
| 🟡 Medium | **Dynamic SQL generation** | Let the LLM select or generate SQL filters based on the user's question, rather than pre-written static queries. |
| 🟡 Medium | **UUID-based user IDs** | Replace `user_{rand}` with `uuid4()` to eliminate collision risk at scale. |
| 🟡 Medium | **Manager-level RBAC** | Department-scoped access — an HR manager sees only their department's employees. |
| 🟢 Low | **Column-level security** | Granular field restrictions — e.g. only payroll admin can see salary, not all HR staff. |
| 🟢 Low | **Streaming responses** | Stream LLM tokens to the frontend for a real-time typing effect via SSE or WebSocket. |
| 🟢 Low | **Frontend build** | Complete the Next.js chat UI with `useChat` hook and role-aware display components. |

---

> 🔥 **Key Insight:** Every layer of this system — the API, the LangGraph agent, the individual nodes — passes the `role` around. But only **`sql_tool.py`** actually enforces it. That single file is the reason an employee cannot see another employee's salary, no matter how the HTTP request is crafted.
