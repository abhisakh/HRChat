# HRChat_LLM — Context-Aware HR Chatbot with RBAC

> A multi-user HR assistant powered by **FastAPI**, **LangGraph**, and **Hybrid AI** (SQL + Vector Search).
> Context aware (aware about the old discussions)
> Every user gets a personalised, role-restricted response. No two users see the same data.

---
## Login Portal

<table>
<tr>
<td align="center" bgcolor="#f3f4f6">

<img width="1492" alt="Screenshot 2026-04-17 at 08 42 06" src="https://github.com/user-attachments/assets/19faa041-a61d-4fb6-a342-9c1cb3c75f71" />

</td>
</tr>
</table>

---

## Scope for an Employee

<table>
<tr>
<td align="center" bgcolor="#f3f4f6">

<img width="1492" alt="Screenshot 2026-04-17 at 08 43 13" src="https://github.com/user-attachments/assets/966a9d12-688b-4994-b2b3-6f70f4369f8c" />


</td>
</tr>
</table>

---

## Scope for a HR

<table>
<tr>
<td align="center" bgcolor="#f3f4f6">

<img width="1492" alt="Screenshot 2026-04-17 at 08 49 41" src="https://github.com/user-attachments/assets/df266332-4a28-44a5-a9fd-0864c25c7252" />

</td>
</tr>
</table>

---
## AI - Transperancy & Audit Trails


<table>
<tr>
<td align="center" bgcolor="#f3f4f6">

<img width="1492" alt="Screenshot 2026-04-17 at 13 57 24" src="https://github.com/user-attachments/assets/91f2da1a-cade-4dcb-92d8-f37aaf048d6b" />

</td>
</tr>
</table>

---

<a id="table-of-contents"></a>

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
  - [Frontend](#️-frontend)
  - [Full Dependency Map](#full-dependency-map)
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
  - [Prerequisites](#prerequisites)
  - [Step 1 — Clone the Repository](#step-1--clone-the-repository)
  - [Step 2 — Create a Python Virtual Environment](#step-2--create-a-python-virtual-environment)
  - [Step 3 — Install Backend Dependencies](#step-3--install-backend-dependencies)
  - [Step 4 — Install Frontend Dependencies](#step-4--install-frontend-dependencies)
  - [Step 5 — Configure Environment Variables](#step-5--configure-environment-variables)
  - [Step 6 — Ingest Policy Documents into Pinecone](#step-6--ingest-policy-documents-into-pinecone)
  - [Step 7 — Seed the Database](#step-7--seed-the-database)
  - [Step 8 — Start the Backend](#step-8--start-the-backend)
  - [Step 9 — Start the Frontend](#step-9--start-the-frontend)
  - [Step 10 — Open the App](#step-10--open-the-app)
  - [Full Setup Summary](#full-setup-summary)
  - [Folder State After Full Setup](#folder-state-after-full-setup)
  - [Common Issues](#common-issues)
- [File Responsibilities](#file-responsibilities)
- [Security Design](#security-design)
- [Current Limitations](#current-limitations)
- [Future Improvements](#future-improvements)
- [Why JWT Authentication Matters](#why-jwt-authentication-matters)
- [Frontend](#frontend)
  - [Folder Structure](#frontend-folder-structure)
  - [Component Architecture](#component-architecture)
  - [File Breakdown](#file-breakdown)
  - [API Layer — api.js](#api-layer--apijs)
  - [State Flow](#state-flow)
  - [UI Design System](#ui-design-system)
  - [Running the Frontend](#running-the-frontend)

---

## Introduction

<a href="#table-of-contents">🔝 Back to Top</a>

**HRChat** is a context-aware, multi-user HR assistant that gives every employee instant, personalised answers to HR questions — while making sure they can only ever see data they are authorised to see.

A typical HR department drowns in repetitive queries: *"How many PTO days do I have?"*, *"What is the parental leave policy?"*, *"Who is my supervisor?"*. These questions pull HR staff away from higher-value work, and employees often wait hours or days for answers that should take seconds. HRChat solves this by acting as an always-available, intelligent first point of contact — routing each question to exactly the right data source and returning a natural-language answer in real time.

What makes HRChat different from a simple FAQ bot is its **Hybrid AI architecture**. HR information lives in two very different places:

- **Structured data** — personal records like salary, PTO balance, hire date, and supervisor — stored in a relational database, specific to each individual employee
- **Unstructured data** — company-wide policies, handbooks, and guidelines — stored as PDF documents that don't fit neatly into rows and columns

Most chatbots handle one or the other. HRChat handles both, automatically routing each question to the right source and combining the result into a single coherent answer.

---

## Why This Project Matters

### The Problem

<a href="#table-of-contents">🔝 Back to Top</a>

Traditional HR support has two failure modes:

**Too slow** — employees submit tickets and wait. HR teams spend the majority of their time answering the same handful of questions repeatedly, leaving less time for strategic work like hiring, retention, and culture.

**Too risky** — giving employees direct database access is dangerous. An employee should be able to ask *"What is my salary?"* but must never be able to see a colleague's salary. A simple chatbot with no access control is a security liability.

### What HRChat Demonstrates

<a href="#table-of-contents">🔝 Back to Top</a>

| Capability | Why It's Non-Trivial |
|---|---|
| **Hybrid retrieval** | Combines SQL (exact, structured) and vector search (semantic, fuzzy) in a single agent. Most systems use one or the other. |
| **Role-based data isolation** | RBAC is enforced at the SQL query level — not in the UI or the LLM prompt — making it impossible to bypass through prompt injection or request forgery. |
| **Persistent per-user memory** | Each user's conversation history is stored and isolated via LangGraph's `SqliteSaver`. The agent remembers context across sessions. |
| **Agentic routing** | A `router_node` classifies each question and sends it down the correct retrieval path. The LLM only generates the final answer — it does not decide where to look. |
| **Audit trail** | Every question and answer is logged with the data source used, giving organisations full visibility into what was asked and what was returned. |

### Who It's For

<a href="#table-of-contents">🔝 Back to Top</a>

- **Employees** — get instant answers to personal HR questions without waiting for a human response
- **HR teams** — reduce repetitive query volume and focus on higher-value work
- **Admins** — full visibility via audit logs and role-management controls
- **Developers** — a working reference implementation of a LangGraph agent with hybrid retrieval, RBAC, and persistent memory

---

## How It Works — Architecture Flow

<a href="#table-of-contents">🔝 Back to Top</a>

### High-Level Flow

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

HRChat spans two ecosystems — a Python backend and a JavaScript frontend. Every technology was chosen for a specific reason, not just familiarity.

---

### 🌐 API Layer

<a href="#table-of-contents">🔝 Back to Top</a>

| Package | Version | Role |
|---|---|---|
| `fastapi` | Latest | Web framework — handles all HTTP endpoints, request validation, and startup events |
| `uvicorn` | Latest | ASGI server that runs the FastAPI app |
| `pydantic` | v2+ | Request/response model validation (`LoginRequest`, `ChatRequest`, `ChatResponse`, etc.) |

**Why FastAPI?** It gives automatic `/docs` Swagger UI, async support, and Pydantic validation out of the box — meaning every endpoint is self-documenting and type-safe with minimal boilerplate.

---

### 🤖 AI & Agent Orchestration

<a href="#table-of-contents">🔝 Back to Top</a>

| Package | Version | Role |
|---|---|---|
| `langgraph` | Latest | `StateGraph` that defines the agent's execution flow — nodes, conditional edges, and memory |
| `langchain-openai` | Latest | OpenAI LLM wrapper (`ChatOpenAI`) used by `generate_node` to write final answers |
| `langchain-pinecone` | Latest | `PineconeVectorStore` used by `retriever.py` to query ingested policy embeddings |
| `langchain-text-splitters` | Latest | `RecursiveCharacterTextSplitter` used by `ingest.py` to chunk PDF text |

**Why LangGraph over a plain LangChain chain?** A linear chain cannot branch. HRChat needs to route questions to different tools depending on intent — that requires a graph with conditional edges. LangGraph also provides `SqliteSaver` for persistent per-user memory at zero extra cost.

---

### 🧠 LLM & Embeddings

<a href="#table-of-contents">🔝 Back to Top</a>

| Model | Provider | Used In | Purpose |
|---|---|---|---|
| `gpt-4o-mini` / `gpt-4` | OpenAI | `generate_node` | Writes natural-language answers from retrieved context |
| `text-embedding-3-small` | OpenAI | `ingest.py` + `retriever.py` | Converts PDF chunks and user queries into 1536-dim vectors for semantic search |

**Why `text-embedding-3-small`?** It produces 1536-dimensional embeddings at a fraction of the cost of `text-embedding-ada-002`, while matching or exceeding its retrieval performance on most benchmarks.

---

### 🗃️ Databases

<a href="#table-of-contents">🔝 Back to Top</a>

| Database | File | Role |
|---|---|---|
| SQLite | `hr_database.db` | Stores `employees`, `users`, and `chat_audit_logs` tables — the core relational data |
| SQLite | `checkpoints.sqlite` | Stores LangGraph conversation checkpoints via `SqliteSaver` — enables per-user persistent memory |
| Pinecone | Cloud index | Stores 1536-dim embeddings of HR policy PDF chunks — enables semantic vector search |

**Why SQLite for development?** It is file-based — zero infrastructure, zero configuration. The SQL schema and queries are compatible with PostgreSQL, so upgrading for production is a connection string change.

**Why two separate SQLite files?** `hr_database.db` is business data — employee records, credentials, audit logs. `checkpoints.sqlite` is agent state — LangGraph conversation memory. Keeping them separate means the agent's memory layer can be wiped or swapped without touching business data.

---

### 📄 PDF Ingestion

<a href="#table-of-contents">🔝 Back to Top</a>

| Package | Role |
|---|---|
| `pypdf` | Extracts raw text from each page of uploaded HR policy PDFs |
| `langchain-text-splitters` | Splits extracted text into overlapping chunks (`chunk_size=1000`, `chunk_overlap=100`) |
| `pinecone` | Python client — creates the index and upserts vector batches of 100 |
| `python-dotenv` | Loads `OPENAI_API_KEY` and `PINECONE_API_KEY` from `.env` during ingestion |
| `hashlib` (stdlib) | MD5 hashes each PDF to detect changes — unchanged files are skipped on re-runs |

---

### 🔐 Security & Auth

<a href="#table-of-contents">🔝 Back to Top</a>

| Tool | Role |
|---|---|
| `hashlib.sha256` (stdlib) | Hashes passwords before storing in the `users` table — plaintext is never written to disk |
| `sqlite3` (stdlib) | Direct DB access with `PRAGMA foreign_keys = ON` — enforces referential integrity |
| Role `CHECK` constraint | SQLite-level enforcement: only `'employee'`, `'hr'`, `'admin'` are valid role values |

> ⚠️ **Known limitation:** SHA-256 is a fast hashing algorithm. Production deployments should replace it with `bcrypt` or `argon2`, which are specifically designed for password hashing and are resistant to brute-force attacks.

---

### 🌱 Data & Dev Tools

<a href="#table-of-contents">🔝 Back to Top</a>

| Package | Role |
|---|---|
| `faker` | Generates realistic fake employee data (names, emails, phone numbers, hire dates) for seeding |
| `random` (stdlib) | Picks random positions, departments, locations, and roles in auto-seed mode |

---

### 🖥️ Frontend

<a href="#table-of-contents">🔝 Back to Top</a>

| Package / Technology | Version | Role |
|---|---|---|
| `react` | 19.0.0 | UI framework — component tree, state management, hooks |
| `react-dom` | 19.0.0 | Renders React component tree into the browser DOM |
| `vite` | 6.0.0 | Dev server + production build tool — replaces Create React App |
| `@vitejs/plugin-react` | 4.3.4 | Enables JSX transform and fast HMR (Hot Module Replacement) in Vite |
| Pure CSS (`App.css`) | — | All styling via CSS custom properties (`:root` variables) — no Tailwind, no Shadcn |
| Native `fetch` API | — | All HTTP calls to FastAPI backend — no Axios dependency |
| `useState` / `useEffect` / `useRef` | — | Chat state, persistent history loading, auto-scroll to latest message |

**Why Vite over Create React App?** Vite uses native ES modules during development — cold starts are near-instant and HMR is file-level. CRA bundles the entire app on every change. For a project this size, Vite is the correct modern choice.

**Why no UI component library?** The design is fully custom to the Umbrella Corp theme — dark sidebar, branded colour palette, role badge colours. Importing Shadcn or Tailwind would add overhead without adding value here.

---

### Full Dependency Map

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

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
├── frontend/                       # Vite + React 19 SPA
│   ├── index.html                  # Vite entry point — mounts <div id="root">
│   ├── package.json                # React 19, Vite 6, @vitejs/plugin-react
│   └── src/
│       ├── main.jsx                # ReactDOM.createRoot — renders <App /> in StrictMode
│       ├── App.jsx                 # Auth gate — Login or ChatWindow based on user state
│       ├── App.css                 # All styles — CSS variables, layout, components
│       ├── components/
│       │   ├── auth/
│       │   │   └── Login.jsx       # Login form — calls loginUser() from api.js
│       │   ├── chat/
│       │   │   ├── ChatWindow.jsx  # Main shell — sidebar, chat tab, audit log tab
│       │   │   └── EmployeeCard.jsx # Structured card for employee profile responses
│       │   └── ui/                 # Reserved for future shared UI components
│       ├── hooks/                  # Reserved for custom hooks (e.g. useChat)
│       └── lib/
│           └── api.js              # All fetch calls — loginUser, sendChatMessage, registerUser
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

<a href="#table-of-contents">🔝 Back to Top</a>

### `main.py` — The API Gateway

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

Two responsibilities:

**`init_db()`** — called on FastAPI startup and by `seed_employees.py`. Reads all `.sql` blueprint files from `/schemas/` and executes them against `hr_database.db`, creating all tables if they don't already exist.

**`save_to_audit_log()`** — called by `audit_node` after every response. Writes `user_id`, `question`, `answer`, and `source` to the `chat_audit_logs` table.

---

## Data Scripts

<a href="#table-of-contents">🔝 Back to Top</a>

### `ingest.py` — PDF to Pinecone

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

> **Design principle:** RBAC is enforced at the **data access layer** (`sql_tool.py`). Even if a client sends a forged `user_id`, the SQL query itself restricts what data is returned. The UI and LLM have no ability to override this.

### The Three Roles

<a href="#table-of-contents">🔝 Back to Top</a>

| Role | Data Access | Admin Actions |
|---|---|---|
| `employee` | Own record only. Salary **always excluded**. | None |
| `hr` | All employee records (`SELECT * FROM employees`) | None |
| `admin` | All employee records + `/delete_user` endpoint | Delete any user and their data |

### How Role Is Determined

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

All endpoints are served at `http://localhost:8000`. Interactive Swagger docs available at `/docs`.

### `POST /login`

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

```json
{ "status": "online" }
```

---

## Database Schema

<a href="#table-of-contents">🔝 Back to Top</a>

Three SQLite tables defined as `.sql` blueprints in `backend/app/db/schemas/`. All are created via `init_db()` on startup using `CREATE TABLE IF NOT EXISTS`, so they are safe to run repeatedly.

### `employees` table (`employees.sql`)

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

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

#### ❓ Why Is `role` in the `users` table and NOT in the `employees` table?

This is a deliberate **separation of concerns** — one of the most important design decisions in the schema.

The `employees` table stores **who you are** as a person inside the organisation:

```
name, position, department, salary, hire_date, supervisor, skills, location
```

The `users` table stores **how you authenticate and what you are allowed to do** inside the system:

```
username, password_hash, role, created_at
```

These are fundamentally different categories of data. Here is why keeping them separate matters:

| Reason | Explanation |
|---|---|
| **Conceptual clarity** | An employee record is an HR record — it describes a person's job. A user record is a system record — it describes a login identity. Mixing them couples two unrelated concerns. |
| **Role ≠ Job title** | An employee's `position` (e.g. `"HR Specialist"`) is a business fact. Their `role` (e.g. `"hr"`) is a system permission. A person can change job title without changing system access, or vice versa. Keeping them separate allows each to change independently. |
| **Security boundary** | Authentication data (`password_hash`, `role`) should be isolated from general HR data (`salary`, `supervisor`). If a query accidentally exposes the `employees` table too broadly, it does not leak password hashes or role assignments. |
| **A person can exist without a login** | An employee record can exist in `employees` before they are ever given system access. The `users` record is only created when they are granted a login. The FK constraint enforces this order — `users` cannot exist without a matching `employees` row, but `employees` can exist without a `users` row. |
| **Future flexibility** | If the system later adds SSO, OAuth, or multi-factor auth, only the `users` table needs to change. The `employees` table — which other parts of the system query for HR data — remains completely unaffected. |

> **In short:** `employees` answers *"Who are you?"*. `users` answers *"What are you allowed to do?"*. Keeping these questions in separate tables is standard database design practice and makes the system more secure, flexible, and maintainable.

---

### `chat_audit_logs` table (`chat_audit_logs.sql`)

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

```
employees (user_id)  ←──── users (user_id)   [FK, enforced by PRAGMA foreign_keys = ON]
employees (user_id)  ←──── chat_audit_logs (user_id)   [soft reference, no FK constraint]
```

Creation order matters: `employees` must be initialised before `users` due to the foreign key dependency.

---

## Environment Variables

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

This section is the **single complete guide** to installing and running both the backend and frontend from scratch. Follow every step in order.

---

### Prerequisites

<a href="#table-of-contents">🔝 Back to Top</a>

You need two separate ecosystems installed — one for Python (backend) and one for Node.js (frontend).

**Backend requirements:**

| Requirement | Version | How to check |
|---|---|---|
| Python | 3.10+ | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any | `git --version` |
| OpenAI API Key | — | Required for LLM + embeddings |
| Pinecone Account | — | Required for vector search |

**Frontend requirements:**

| Requirement | Version | How to check |
|---|---|---|
| Node.js | 18+ | `node -v` |
| npm | 8+ | `npm -v` |

> If Node.js is not installed, go to [https://nodejs.org](https://nodejs.org) and download the **LTS** version. Installing Node.js also installs npm automatically.

---

### Step 1 — Clone the Repository

<a href="#table-of-contents">🔝 Back to Top</a>

```bash
git clone https://github.com/abhisakh/HRChat.git
cd HRChat
```

All backend commands in the steps below must be run from this project root (`HRChat/`).

---

### Step 2 — Create a Python Virtual Environment

<a href="#table-of-contents">🔝 Back to Top</a>

```bash
# Create the environment
python -m venv venv

# Activate — macOS / Linux
source venv/bin/activate

# Activate — Windows
venv\Scriptsctivate
```

You should see `(venv)` at the start of your terminal prompt once activated. Keep this terminal open — all Python commands run inside it.

---

### Step 3 — Install Backend Dependencies

<a href="#table-of-contents">🔝 Back to Top</a>

```bash
# Run from project root with venv activated
pip install -r requirements.txt
```

Key packages installed:

| Package | Purpose |
|---|---|
| `fastapi` + `uvicorn` | API framework + ASGI server |
| `langgraph` | LangGraph agent orchestration |
| `langchain-openai` | LLM + embeddings via OpenAI |
| `langchain-pinecone` | Pinecone vector store integration |
| `pypdf` | PDF text extraction for ingestion |
| `faker` | Fake employee data for seeding |
| `python-dotenv` | `.env` file loading |
| `pydantic` | Request/response validation |

---

### Step 4 — Install Frontend Dependencies

<a href="#table-of-contents">🔝 Back to Top</a>

> ⚠️ Frontend commands **must** be run from inside the `frontend/` directory — not the project root. Vite resolves all paths relative to where you run the command.

```bash
# Navigate into the frontend directory
cd frontend

# Install React 19, Vite 6, and @vitejs/plugin-react
npm install
```

This creates `frontend/node_modules/` — never commit this folder (it is in `.gitignore`). You only need to run `npm install` once after cloning, or again if `package.json` changes.

Expected output:

```
added 243 packages in 12s
```

After `npm install`, go back to the project root for the remaining steps:

```bash
cd ..
```

---

### Step 5 — Configure Environment Variables

<a href="#table-of-contents">🔝 Back to Top</a>

```bash
# Run from project root
cp .env.example .env
```

Open `.env` and fill in your API keys:

```env
# OpenAI — used for LLM responses and text embeddings
OPENAI_API_KEY=sk-...

# Pinecone — used for storing and searching HR policy documents
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=hrchat-policies
```

> ⚠️ Never commit `.env` to version control. It is already listed in `.gitignore`.

---

### Step 6 — Ingest Policy Documents into Pinecone

<a href="#table-of-contents">🔝 Back to Top</a>

Drop your HR policy PDF files into `data/raw/`, then run from the project root:

```bash
python data/scripts/ingest.py
```

Expected output:

```
⚙️  Processing umbrella_corp_policies.pdf...
✅ Indexed umbrella_corp_policies.pdf
```

Already-indexed unchanged files are skipped on re-runs via MD5 manifest. To force re-index, delete the entry from `data/scripts/ingest_manifest.json`.

---

### Step 7 — Seed the Database

<a href="#table-of-contents">🔝 Back to Top</a>

```bash
# Run from project root
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

---

### Step 8 — Start the Backend

<a href="#table-of-contents">🔝 Back to Top</a>

```bash
# Run from project root
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

| Flag | What it does |
|---|---|
| `backend.main:app` | Points Uvicorn to the `app` object inside `backend/main.py` |
| `--reload` | Auto-restarts on code changes (dev only — remove in production) |
| `--host 0.0.0.0` | Accessible on your local network, not just `localhost` |
| `--port 8000` | Serves on port 8000 |

Expected output:

```
Initializing HR Databases...
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

Two SQLite files are auto-created on first startup:
- `hr_database.db` — created by `init_db()` via `connection.py`
- `checkpoints.sqlite` — created by LangGraph `SqliteSaver` on first `/chat` call

**Leave this terminal running.** Open a new terminal for the next step.

---

### Step 9 — Start the Frontend

<a href="#table-of-contents">🔝 Back to Top</a>

Open a **new terminal window**, navigate into the `frontend/` directory, then start Vite:

```bash
# Open a NEW terminal — do NOT stop the backend
cd HRChat/frontend
npm run dev
```

Expected output:

```
  VITE v6.x.x  ready in Xms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
```

> ⚠️ The backend must already be running on port 8000 before you open the frontend. All API calls in `api.js` point to `http://localhost:8000`.

---

### Step 10 — Open the App

<a href="#table-of-contents">🔝 Back to Top</a>

Open your browser and go to:

```
http://localhost:5173
```

You should see the **Umbrella Corp HR Login** screen. Log in with any seeded username and the password `password123`.

To verify the backend is also healthy:

```bash
curl http://localhost:8000/health
# {"status":"online"}
```

Full API docs available at: `http://localhost:8000/docs`

---

### Full Setup Summary

<a href="#table-of-contents">🔝 Back to Top</a>

```
Terminal 1 (project root, venv activated)        Terminal 2 (frontend/ directory)
─────────────────────────────────────────        ────────────────────────────────
git clone ...  &&  cd HRChat
python -m venv venv  &&  source venv/activate
pip install -r requirements.txt
                                                 cd HRChat/frontend
                                                 npm install
                                                 cd ..  (back to root)
cp .env.example .env  →  fill in API keys
python data/scripts/ingest.py
python data/scripts/seed_employees.py
uvicorn backend.main:app --reload \              npm run dev
  --host 0.0.0.0 --port 8000
  ↑ keep running                                  ↑ keep running

Backend: http://localhost:8000                   Frontend: http://localhost:5173
API docs: http://localhost:8000/docs
```

---

### Folder State After Full Setup

<a href="#table-of-contents">🔝 Back to Top</a>

```
HRChat/
├── backend/app/db/
│   ├── hr_database.db          ← created by init_db() on first backend startup
│   └── checkpoints.sqlite      ← created by LangGraph on first /chat call
├── frontend/
│   └── node_modules/           ← created by npm install (do not commit)
└── data/scripts/
    └── ingest_manifest.json    ← updated by ingest.py after each PDF is indexed
```

---

### Common Issues

<a href="#table-of-contents">🔝 Back to Top</a>

**Backend:**

| Problem | Likely Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: backend` | Running from wrong directory | Run all Python commands from project root (`HRChat/`) |
| `sqlite3.OperationalError: no such table` | DB not initialised | Run `seed_employees.py` or start the server — `init_db()` runs on startup |
| `pinecone.exceptions.NotFoundException` | Index name mismatch | Check `PINECONE_INDEX_NAME` in `.env` matches Pinecone dashboard |
| `openai.AuthenticationError` | Invalid API key | Double-check `OPENAI_API_KEY` in `.env` |
| `Port 8000 already in use` | Another process on that port | Use `--port 8001` or kill the existing process |

**Frontend:**

| Problem | Likely Cause | Fix |
|---|---|---|
| `npm: command not found` | Node.js not installed | Download LTS from [nodejs.org](https://nodejs.org) |
| `Cannot find module 'vite'` | `npm install` not run yet | Run `npm install` from inside `frontend/` |
| `ERR_MODULE_NOT_FOUND` | Running npm from wrong directory | `cd frontend` first, then retry |
| Blank page at `localhost:5173` | Backend not running | Start uvicorn first, then refresh the page |
| `CORS error` in browser console | Backend not allowing frontend origin | Add CORS middleware to `main.py` for `http://localhost:5173` |
| Login always fails | Backend not seeded | Run `seed_employees.py` to create test users |
---

## File Responsibilities

<a href="#table-of-contents">🔝 Back to Top</a>

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

<a href="#table-of-contents">🔝 Back to Top</a>

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
| **DB** | `role` stored in `users` table, not `employees` — separates authentication data from HR data, so a broad `employees` query can never leak role assignments or password hashes | `auth.sql` |
| **Memory** | `thread_id = user_id` — conversation history is per-user isolated | `graph.py` |

---

## Current Limitations

<a href="#table-of-contents">🔝 Back to Top</a>

- **No JWT** — `user_id` is passed in the request body. The SQL layer still restricts data by role, but a client could attempt to send any `user_id` string.
- **SHA-256 password hashing** — SHA-256 is fast, making brute-force attacks cheaper. Production should use `bcrypt` or `argon2`.
- **Static SQL queries** — `sql_tool.py` runs pre-written queries. It does not yet dynamically interpret natural language into SQL.
- **HR and Admin read access are identical** — both run `SELECT * FROM employees`. Admin's extra privilege is only the `/delete_user` endpoint.
- **No logout / token invalidation** — there is no session or token mechanism to invalidate yet.
- **`user_id` collision risk** — IDs are `user_{random 4-digit number}`. With many users, ID collisions become likely. UUIDs should replace this pattern.

---

## Future Improvements

<a href="#table-of-contents">🔝 Back to Top</a>

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

## Why JWT Authentication Matters

<a href="#table-of-contents">🔝 Back to Top</a>

HRChat currently identifies users by passing `user_id` as a plain string in the request body. JWT (JSON Web Token) authentication would replace this with a cryptographically signed token — and the difference is significant at every layer of the architecture.

---

### The Current Problem — Trusting a Plain `user_id`

Right now, the `/chat` endpoint receives this:

```json
{
  "user_id": "user_4821",
  "message": "What is my salary?"
}
```

The server takes `user_id` at face value, looks up the role from the DB, and runs the query. The SQL layer (`sql_tool.py`) still restricts *what data* comes back — so even if someone sends `user_id: "user_0001"` (someone else's ID), they only get that user's non-salary fields.

But the problem is **identity spoofing** — a malicious user can impersonate any `user_id` they can guess. The data they get back is still RBAC-restricted, but they are now reading someone else's employment record (name, position, PTO, supervisor, department). That is a privacy violation even without salary exposure.

```
Current flow — vulnerable to spoofing:

Client sends: { "user_id": "user_4821" }   ← anyone can type any ID
                     ↓
main.py: get_user_role("user_4821")         ← role fetched, but ID not verified
                     ↓
sql_tool.py: WHERE user_id = "user_4821"   ← correct restriction, wrong identity
```

---

### How JWT Fixes This

After a successful `/login`, the server would issue a **signed JWT token** containing the user's identity and role:

```json
{
  "sub": "user_4821",
  "role": "employee",
  "exp": 1780000000
}
```

This token is signed with a secret key only the server knows. The client stores it and sends it with every request in the `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

The server verifies the signature on every request — if the token has been tampered with, the signature check fails and the request is rejected immediately.

```
JWT flow — identity is verified:

Client sends: Authorization: Bearer <signed_token>
                     ↓
main.py: decode_token(token)
  → verifies signature  ← cannot be forged without the secret key
  → extracts user_id + role from payload
  → no DB lookup needed for role
                     ↓
sql_tool.py: WHERE user_id = verified_user_id   ← identity is now trustworthy
```

---

### How JWT Would Change Each Layer of HRChat

| Layer | Current behaviour | With JWT |
|---|---|---|
| **`/login`** | Returns `user_id` + `role` as plain JSON | Returns a signed JWT token containing `user_id` + `role` + expiry |
| **`/chat`** | Accepts `user_id` from request body — not verified | Reads JWT from `Authorization` header — signature verified before any logic runs |
| **`main.py`** | Calls `get_user_role(user_id)` — one DB query per request | Decodes JWT payload — role is already inside the token, no DB lookup needed |
| **`graph.py`** | Injects role from DB result | Injects role from verified JWT payload — same code, more trustworthy input |
| **`sql_tool.py`** | RBAC enforced, but `user_id` could be spoofed | RBAC enforced with a `user_id` that has been cryptographically verified |
| **Logout** | No mechanism — nothing to invalidate | Token has an `exp` (expiry) field — short-lived tokens expire automatically |

---

### What a JWT Implementation Would Look Like in HRChat

**Generating the token at login (`main.py`):**

```python
import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET")

def create_token(user_id: str, role: str) -> str:
    payload = {
        "sub":  user_id,
        "role": role,
        "exp":  datetime.utcnow() + timedelta(hours=8)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

@app.post("/login")
async def login(request: LoginRequest):
    user = verify_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user["user_id"], user["role"])
    return { "access_token": token, "token_type": "bearer" }
```

**Verifying the token on every protected request (`main.py`):**

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, Security

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return { "user_id": payload["sub"], "role": payload["role"] }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, token_data: dict = Depends(verify_token)):
    # user_id and role now come from the verified token — not the request body
    user_id = token_data["user_id"]
    user_role = token_data["role"]

    config = {
        "configurable": {
            "thread_id": user_id,
            "role": user_role        # ← verified, cannot be spoofed
        }
    }
    ...
```

**New environment variable needed:**

```env
JWT_SECRET=your-long-random-secret-key-here
```

---

### JWT Security Properties That HRChat Gains

| Property | What it means for HRChat |
|---|---|
| **Stateless authentication** | The server does not need to look up the session in a DB on every request — the token is self-contained. Reduces DB load at scale. |
| **Tamper detection** | If anyone modifies the `user_id` or `role` inside the token, the signature check fails instantly. Identity spoofing becomes cryptographically impossible. |
| **Automatic expiry** | The `exp` field means tokens become invalid after a set time (e.g. 8 hours). No explicit logout needed — the token simply stops working. |
| **Role embedded in token** | `get_user_role(user_id)` DB call is eliminated on every `/chat` request. Role is read directly from the verified payload. |
| **Standard and interoperable** | JWT is an open standard (RFC 7519). Any frontend — Next.js, mobile app, third-party client — can consume it without custom session logic. |

---

### What JWT Does NOT Solve

JWT is not a silver bullet. These limitations would remain even after adding JWT to HRChat:

- **SHA-256 password hashing** — still needs to be replaced with `bcrypt` or `argon2` at the `/login` step
- **Token revocation** — a signed token is valid until it expires. If a user's role changes mid-session, their token still carries the old role until expiry. A token blacklist or short expiry window is needed to handle this
- **RBAC enforcement** — JWT only verifies identity. `sql_tool.py` still needs to enforce what each role can see — JWT does not replace this

> 🔐 **Summary:** JWT does not change *what* users can access — `sql_tool.py` controls that. JWT changes *whether we can trust who they claim to be*. Both layers are necessary for a fully secure system.

---

## Frontend

<a href="#table-of-contents">🔝 Back to Top</a>

The frontend is a **Vite + React 19** single-page application styled with pure CSS — no Tailwind, no UI component library. It communicates directly with the FastAPI backend via `fetch` calls centralised in a single `api.js` module.

---

<a id="frontend-folder-structure"></a>
### Folder Structure

<a href="#table-of-contents">🔝 Back to Top</a>

```
frontend/
├── index.html                  # Vite entry point — mounts <div id="root">
├── package.json                # Dependencies: React 19, Vite 6
├── src/
│   ├── main.jsx                # ReactDOM.createRoot — renders <App /> in StrictMode
│   ├── App.jsx                 # Root component — auth gate (Login vs ChatWindow)
│   ├── App.css                 # Global styles — CSS variables, layout, all components
│   ├── components/
│   │   ├── auth/
│   │   │   └── Login.jsx       # Login form — calls loginUser() from api.js
│   │   ├── chat/
│   │   │   ├── ChatWindow.jsx  # Main app shell — sidebar, chat, audit log tabs
│   │   │   └── EmployeeCard.jsx # Structured card rendered for employee profile responses
│   │   └── ui/                 # (empty — reserved for future shared UI components)
│   ├── hooks/                  # (empty — reserved for custom hooks e.g. useChat)
│   └── lib/
│       └── api.js              # Single API module — loginUser, sendChatMessage, registerUser
```

---

<a id="component-architecture"></a>
### Component Architecture

<a href="#table-of-contents">🔝 Back to Top</a>

```
<App>
  │
  ├── user === null  →  <Login onLoginSuccess={handleLogin} />
  │                         │
  │                         └── calls loginUser() from api.js
  │                             on success → sets user state in App
  │
  └── user !== null  →  <ChatWindow user={user} onLogout={handleLogout} />
                              │
                              ├── Sidebar
                              │     ├── Logo + branding (☂️ Umbrella HR)
                              │     ├── User avatar + role badge
                              │     ├── Nav tabs: 💬 Chat  |  📜 Audit Logs
                              │     └── Sign Out button → calls onLogout → clears user state
                              │
                              ├── Tab: Chat
                              │     ├── messages.map() → message bubbles
                              │     │     ├── user bubble  (blue, right-aligned)
                              │     │     ├── assistant bubble  (white, left-aligned)
                              │     │     └── <EmployeeCard />  (when response is JSON profile)
                              │     ├── Typing indicator  ("Searching encrypted database...")
                              │     └── Input form + Send button
                              │
                              └── Tab: Audit Logs
                                    └── Fetches /audit/logs/{user_id}
                                        → renders table with Q&A, source badge,
                                          node_path, security status, timestamp
```

---

<a id="file-breakdown"></a>
### File Breakdown

<a href="#table-of-contents">🔝 Back to Top</a>

#### `index.html`

Standard Vite entry point. Contains only `<div id="root">` and a `<script type="module">` pointing to `src/main.jsx`. No stylesheets, no meta tags added yet.

---

#### `main.jsx`

Bootstraps the React app using `ReactDOM.createRoot` (React 18+ API, used here with React 19). Wraps the entire app in `React.StrictMode` — surfaces side-effect bugs and deprecated API usage during development.

```jsx
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

---

#### `App.jsx` — The Auth Gate

Holds the single piece of global state: `user`. This is `null` on load and gets set when login succeeds.

```jsx
const [user, setUser] = useState(null);

// null → show Login
// object → show ChatWindow
return (
  <div className="app-container">
    {!user ? (
      <Login onLoginSuccess={handleLogin} />
    ) : (
      <ChatWindow user={user} onLogout={handleLogout} />
    )}
  </div>
);
```

`handleLogout` simply sets `user` back to `null`, which re-renders the login screen — no router needed.

---

#### `Login.jsx` — Authentication Form

Controlled form with two inputs (`username`, `password`). On submit, calls `loginUser()` from `api.js`. On success, calls `onLoginSuccess(data)` which sets the `user` state in `App.jsx`. On failure, displays an inline error message.

**Key detail:** `onLoginSuccess` receives the full response object `{ user_id, role, status }` from the backend — this object becomes the `user` prop passed into `ChatWindow`.

```jsx
const data = await loginUser(username, password);
onLoginSuccess(data);  // { user_id: "user_4821", role: "employee", status: "success" }
```

---

#### `ChatWindow.jsx` — The Main Application Shell

The most complex component. Manages four pieces of state:

| State | Type | Purpose |
|---|---|---|
| `messages` | Array | Chat history — both user and assistant messages |
| `auditLogs` | Array | Fetched from `/audit/logs/{user_id}` when audit tab is active |
| `input` | String | Controlled input field value |
| `isTyping` | Boolean | Shows typing indicator, disables input while waiting for response |
| `activeTab` | String | `'chat'` or `'audit'` — controls which view renders |

**Three `useEffect` hooks:**

```jsx
// 1. Load chat history on mount (persistent memory)
useEffect(() => {
  fetch(`/chat/history/${user.user_id}`) → setMessages(data.history)
}, [user.user_id]);

// 2. Load audit logs when audit tab is opened
useEffect(() => {
  if (activeTab === 'audit')
    fetch(`/audit/logs/${user.user_id}`) → setAuditLogs(data.logs)
}, [activeTab, user.user_id]);

// 3. Auto-scroll to latest message
useEffect(() => {
  scrollRef.current?.scrollIntoView({ behavior: "smooth" })
}, [messages, isTyping]);
```

**Smart message rendering** — detects if an assistant response is a JSON employee profile and renders `<EmployeeCard />` instead of a plain text bubble:

```jsx
const isEmployeeCard = msg.role === 'assistant' &&
  (typeof msg.content === 'object' ||
  (typeof msg.content === 'string' && msg.content.includes('"user_id"')));

// Renders either:
<EmployeeCard data={msg.content} />   // structured profile card
// or:
<div className="message-bubble">{msg.content}</div>  // plain text bubble
```

**Audit log table columns:** Exchange (Q&A preview), Origin (`SQL` / `DOC` badge), Execution Path (`node_path` in monospace), Security Status (coloured badge), Timestamp (localised).

---

#### `EmployeeCard.jsx` — Structured Profile Response

Rendered instead of a text bubble when the backend returns employee profile data. Safely parses the response whether it arrives as a JSON object or a JSON string (handles LLM inconsistency):

```jsx
const profile = typeof data === 'string' ? JSON.parse(data) : data;
```

**Displays:**
- Initials avatar (`first_name[0] + last_name[0]`)
- Name + position
- Location, department, email
- Skills — split by comma, each rendered as a `<span className="skill-tag">`
- Salary — **only rendered if present** in the response (`profile.salary &&`) — this means RBAC is respected automatically: employees won't see this field because the backend never sends it

```jsx
{profile.salary && (
  <div className="salary-info">
    💰 Annual Salary: ${profile.salary.toLocaleString()}
  </div>
)}
```

---

<a id="api-layer--apijs"></a>
### API Layer — `api.js`

<a href="#table-of-contents">🔝 Back to Top</a>

Single source of truth for all backend communication. All functions are named exports — no default export — so they are imported individually where needed.

```
BASE_URL = "http://localhost:8000"
```

| Function | Endpoint | Method | Used In | Returns |
|---|---|---|---|---|
| `loginUser(username, password)` | `/login` | POST | `Login.jsx` | `{ user_id, role, status }` |
| `sendChatMessage(userId, message)` | `/chat` | POST | `api.js` (defined but `ChatWindow` uses fetch directly) | `{ user_id, answer, source }` |
| `registerUser(userData)` | `/register` | POST | Not yet wired to a UI component | `{ status, user_id, role }` |

> **Note:** `ChatWindow.jsx` currently calls `fetch` directly rather than using `sendChatMessage()` from `api.js`. This is a minor inconsistency — consolidating all fetch calls through `api.js` would be a clean improvement.

---

<a id="state-flow"></a>
### State Flow

<a href="#table-of-contents">🔝 Back to Top</a>

```
App.jsx
  user: null
      │
      │  Login.jsx calls loginUser()
      │  Backend returns { user_id, role, status }
      │  handleLogin(data) → user = { user_id, role, status }
      ▼
App.jsx
  user: { user_id: "user_4821", role: "employee", status: "success" }
      │
      │  Passed as props into ChatWindow
      ▼
ChatWindow.jsx
  props.user.user_id  → used in fetch URLs (/chat, /audit/logs)
  props.user.role     → shown in role badge, sent in chat POST body
  props.user.first_name → shown in avatar and welcome message
      │
      │  User types message → handleSendMessage()
      │  POST /chat { user_id, message, role }
      │  Response { answer, source } → appended to messages[]
      ▼
messages[] re-renders
  → plain text bubble  OR  <EmployeeCard /> depending on content type
```

---

<a id="ui-design-system"></a>
### UI Design System

<a href="#table-of-contents">🔝 Back to Top</a>

All styles live in a single `App.css` file using CSS custom properties defined in `:root`:

```css
:root {
  --bg-dark:       #121417;   /* Sidebar background */
  --bg-light:      #e5e9ed;   /* Chat area background */
  --umbrella-red:  #237cc5;   /* Primary accent (blue, named for theming) */
  --border-color:  #7c97b1;   /* Input borders, table lines */
  --text-dark:     #2d3436;   /* Primary text */
  --text-muted:    #636e72;   /* Secondary text, disclaimers */
}
```

**Layout:** Two-column flexbox — fixed-width sidebar (`min 360px, max 420px`) + fluid chat area (`flex: 1`).

**Role badges** — colour-coded by role value:

```css
.role-badge.hr       { background: #ffd700; color: #000; }  /* Gold */
.role-badge.employee { background: #00b894; color: #fff; }  /* Green */
```

**Source badges in audit log** — colour-coded by data source:

```
SQL origin  →  blue  (#0288d1)  —  "🔒 DB Record"
DOC origin  →  purple (#7b1fa2) —  "📄 Doc Search"
```

**EmployeeCard** — rendered outside the standard message bubble with a red left border (`border-left: 8px solid #d63031`), heavy drop shadow, and a `slideIn` CSS animation on mount.

---

<a id="running-the-frontend"></a>
### Running the Frontend

<a href="#table-of-contents">🔝 Back to Top</a>

> ⚠️ **Important:** The frontend runs in the **Node.js ecosystem** — completely separate from Python/pip. If you have only used Python so far, you will need to install Node.js before anything else. All frontend commands must also be run from **inside the `frontend/` directory**, not from the project root.

---

#### Prerequisites — Install Node.js and npm

The frontend requires **Node.js** (the JavaScript runtime) and **npm** (Node Package Manager). These are equivalent to Python and pip — but for JavaScript.

**Check if you already have them:**

```bash
node -v   # should print v18.0.0 or higher
npm -v    # should print 8.0.0 or higher
```

**If not installed:**

Go to [https://nodejs.org](https://nodejs.org) and download the **LTS (Long Term Support)** version. Installing Node.js also installs npm automatically. Vite and React do **not** need to be installed globally — they are installed as project dependencies in the next step.

---

#### If Starting the Frontend from Scratch

If the `frontend/` folder has the source files but no `node_modules/` yet (i.e. you just cloned the repo), follow these steps:

**Step 1 — Navigate into the frontend directory:**

```bash
cd frontend
```

> Always `cd frontend` first. Every npm command reads `package.json` and resolves paths relative to the directory you are in. Running npm from the project root will fail because there is no `package.json` there.

**Step 2 — Verify `package.json` is correct:**

The `package.json` in `frontend/` should look exactly like this. If it doesn't, replace it:

```json
{
  "name": "frontend",
  "version": "1.0.0",
  "description": "Umbrella Corp HR Portal Frontend",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "vite": "^6.0.0"
  }
}
```

Key things to check:
- `"type": "module"` must be present — this tells Node.js to treat `.js` files as ES modules (required for Vite)
- `vite` and `@vitejs/plugin-react` are in `devDependencies` — they are build tools, not shipped to production
- React and React DOM are in `dependencies` — they are shipped

**Step 3 — Install all dependencies:**

```bash
npm install
```

This reads `package.json` and downloads React 19, Vite 6, and `@vitejs/plugin-react` into `frontend/node_modules/`. This folder is created automatically — never commit it to Git (it is listed in `.gitignore`).

You only need to run `npm install` once after cloning, or again whenever `package.json` changes.

---

#### Running the Dev Server

```bash
# Make sure you are inside frontend/
cd frontend
npm run dev
```

Vite will serve the app at **`http://localhost:5173`** by default. You will see:

```
  VITE v6.x.x  ready in Xms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
```

> ⚠️ Make sure the FastAPI backend is already running on `http://localhost:8000` before opening the frontend — all API calls in `api.js` are hardcoded to that address.

---

#### Build for Production

```bash
# Must be inside frontend/
cd frontend
npm run build
# Output goes to frontend/dist/
```

---

#### Full Stack — Running Both at Once (Recommended Workflow)

Open **two separate terminal windows**:

```bash
# Terminal 1 — Backend
# Run from project root (HRChat/)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# Terminal 2 — Frontend
# Must cd into frontend/ first
cd frontend
npm run dev
```

Then open **`http://localhost:5173`** in your browser.

---

#### Quick Reference — Where to Run Each Command

| Command | Directory | Why |
|---|---|---|
| `uvicorn backend.main:app ...` | Project root `HRChat/` | Python resolves `backend.main` as a package path from root |
| `npm install` | `HRChat/frontend/` | Reads `frontend/package.json`, creates `frontend/node_modules/` |
| `npm run dev` | `HRChat/frontend/` | Vite resolves `src/`, `index.html` relative to `frontend/` |
| `npm run build` | `HRChat/frontend/` | Output written to `frontend/dist/` |
| `python data/scripts/ingest.py` | Project root `HRChat/` | Resolves `data/raw/` and `.env` relative to root |
| `python data/scripts/seed_employees.py` | Project root `HRChat/` | Imports `backend.app.db.connection` as a Python module |

---

#### Common Frontend Issues

| Problem | Likely Cause | Fix |
|---|---|---|
| `npm: command not found` | Node.js not installed | Download LTS from [nodejs.org](https://nodejs.org) |
| `Cannot find module 'vite'` | `npm install` not run yet | Run `npm install` from inside `frontend/` |
| `ERR_MODULE_NOT_FOUND` | Running npm from wrong directory | `cd frontend` first, then retry |
| `"type": "module" missing` | `package.json` missing module type | Add `"type": "module"` to `package.json` |
| Blank page at `localhost:5173` | Backend not running | Start uvicorn first, then refresh |
| `CORS error` in browser console | Backend not allowing frontend origin | Add CORS middleware to `main.py` for `http://localhost:5173` |

---

> 🔥 **Key Insight:** Every layer of this system — the API, the LangGraph agent, the individual nodes — passes the `role` around. But only **`sql_tool.py`** actually enforces it. That single file is the reason an employee cannot see another employee's salary, no matter how the HTTP request is crafted.
