#backend/main.py
import uvicorn
import sqlite3
import hashlib
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
from typing import List, Optional

# LangChain / Agent Imports
from backend.app.agent.graph import hr_agent
from backend.app.db.connection import init_db, save_to_audit_log
from langchain_core.messages import HumanMessage, AIMessage
from fastapi.middleware.cors import CORSMiddleware

# --- 0. Configuration ---
DB_PATH = Path(__file__).parent / "app" / "db" / "hr_database.db"

app = FastAPI(
    title="HRChat API",
    description="Multi-user HR Assistant with RBAC and Contextual Memory",
    version="2.2.0"
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. Startup ---
@app.on_event("startup")
async def startup_event():
    print("Initializing Umbrella HR Databases...")
    init_db()

# --- 2. Models ---

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    user_id: str
    message: str
    # This history field captures the conversation thread from React
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    user_id: str
    answer: str
    source: str

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    admin_id: str
    username: str
    password: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    position: str
    department: str
    skills: str
    location: str
    hire_date: str
    supervisor: str
    salary: float
    role: str = "employee"
    available_pto: int

# --- 3. DB Helpers ---

def get_connection():
    # Adding a 20-second timeout to wait for locks to clear
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # This mode is much better for concurrent access (Read/Write)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

# def verify_user(username, password):
#     password_hash = hashlib.sha256(password.encode()).hexdigest()
#     conn = get_connection()
#     cursor = conn.cursor()
#     query = """
#         SELECT u.user_id, u.role, e.first_name
#         FROM users u
#         JOIN employees e ON u.user_id = e.user_id
#         WHERE u.username = ? AND u.password_hash = ?
#     """
#     cursor.execute(query, (username, password_hash))
#     result = cursor.fetchone()
#     conn.close()
#     if result:
#         return {"user_id": result["user_id"], "role": result["role"], "first_name": result["first_name"]}
#     return None

def verify_user(username, password):
    # REMOVE THIS LINE: password_hash = hashlib.sha256(password.encode()).hexdigest()
    # The 'password' variable coming from React IS already the hash.

    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT u.user_id, u.role, e.first_name
        FROM users u
        JOIN employees e ON u.user_id = e.user_id
        WHERE u.username = ? AND u.password_hash = ?
    """
    # Use the 'password' directly as the hash
    cursor.execute(query, (username, password))
    result = cursor.fetchone()
    conn.close()

    if result:
        return {"user_id": result["user_id"], "role": result["role"], "first_name": result["first_name"]}
    return None

def get_user_role(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result["role"] if result else "employee"

def get_memory_by_user(user_id: str):
    """Retrieves history from database for page refreshes."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT question, answer
        FROM chat_audit_logs
        WHERE user_id = ?
        ORDER BY timestamp ASC
    """
    try:
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()
        history = []
        for row in rows:
            history.append({"role": "user", "content": row["question"]})
            history.append({"role": "assistant", "content": row["answer"]})
        return history
    except Exception:
        return []
    finally:
        conn.close()

# --- 4. Endpoints ---

@app.post("/login")
async def login(request: LoginRequest):
    user = verify_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {**user, "status": "success"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # 1. Validate User & Role
        user_role = get_user_role(request.user_id)
        if not user_role:
            raise HTTPException(status_code=403, detail="User role not found.")

        # 2. Context Restoration & Deduplication Logic
        # If frontend history is empty (e.g., refresh/re-login), pull from DB
        effective_history = request.history
        if not effective_history or len(effective_history) == 0:
            raw_db_history = get_memory_by_user(request.user_id)
            effective_history = [
                ChatMessage(role=m["role"], content=m["content"])
                for m in raw_db_history[-10:] # Last 10 messages for context
            ]

        # 3. Convert to LangChain Format
        formatted_messages = []
        for msg in effective_history:
            if msg.role.lower() in ["user", "human"]:
                formatted_messages.append(HumanMessage(content=msg.content))
            else:
                formatted_messages.append(AIMessage(content=msg.content))

        # Add the current user query
        formatted_messages.append(HumanMessage(content=request.message))

        # 4. State Management & Invocation
        # We use a unique thread_id.
        # To avoid duplication with LangGraph's internal SqliteSaver:
        # We pass the full history into the 'messages' key.
        config = {"configurable": {"thread_id": request.user_id, "role": user_role}}

        # We 'update' the state explicitly to ensure the graph uses our curated list
        initial_state = {"messages": formatted_messages}

        # Invoke the Agent
        final_state = hr_agent.invoke(initial_state, config=config)

        # 5. Safety Check for Missing Data
        answer = final_state.get("answer", "I'm sorry, I encountered an error generating a response.")
        source = final_state.get("source_used", "unknown")
        # Ensure node_path is a list before joining
        steps = final_state.get("steps", ["start", "process", "end"])
        path_str = " -> ".join(steps) if isinstance(steps, list) else str(steps)

        # 6. Final Audit & Response
        save_to_audit_log(
            user_id=request.user_id,
            question=request.message,
            answer=answer,
            source=source,
            node_path=path_str
        )

        return ChatResponse(
            user_id=request.user_id,
            answer=answer,
            source=source
        )

    except Exception as e:
        # Log the actual error to console for debugging
        print(f"--- [CRITICAL ERROR] --- \nType: {type(e).__name__} \nDetail: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/chat/history/{user_id}")
async def chat_history(user_id: str):
    history = get_memory_by_user(user_id)
    return {"history": history}

@app.get("/audit/logs/{user_id}")
async def audit_logs(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT id, question, answer, source_used, node_path, timestamp
        FROM chat_audit_logs
        WHERE user_id = ?
        ORDER BY timestamp DESC
    """
    cursor.execute(query, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return {"logs": [dict(row) for row in rows]}


# @app.post("/register")
# async def register(request: RegisterRequest):
#     conn = get_connection()
#     cursor = conn.cursor()

#     # 1. LOOPHOLE FIX: Verify the requester is actually an ADMIN or HR
#     cursor.execute("SELECT role FROM users WHERE user_id = ?", (request.admin_id,))
#     admin_record = cursor.fetchone()

#     if not admin_record or admin_record["role"] not in ["admin", "hr"]:
#         conn.close()
#         raise HTTPException(status_code=403, detail="Unauthorized: Only Admin/HR can register employees.")

#     # 2. Check if username exists
#     cursor.execute("SELECT username FROM users WHERE username = ?", (request.username,))
#     if cursor.fetchone():
#         conn.close()
#         raise HTTPException(status_code=400, detail="Username already taken")

#     try:
#         # Unique ID generation logic (from previous patch)
#         while True:
#             new_id = f"user_{random.randint(1000, 9999)}"
#             cursor.execute("SELECT user_id FROM employees WHERE user_id = ?", (new_id,))
#             if not cursor.fetchone(): break

#         # 3. Create records using the Admin-defined role
#         cursor.execute("""
#             INSERT INTO employees (user_id, first_name, last_name, position, salary)
#             VALUES (?, ?, ?, ?, ?)
#         """, (new_id, request.first_name, request.last_name, request.position, request.salary))

#         password_hash = hashlib.sha256(request.password.encode()).hexdigest()
#         cursor.execute("""
#             INSERT INTO users (user_id, username, password_hash, role)
#             VALUES (?, ?, ?, ?)
#         """, (new_id, request.username, password_hash, request.role))

#         conn.commit()
#         return {"status": "success", "user_id": new_id, "assigned_role": request.role}
#     except Exception as e:
#         conn.rollback()
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         conn.close()

@app.post("/register")
async def register(request: RegisterRequest):
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Authority Check
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (request.admin_id,))
    admin_record = cursor.fetchone()

    if not admin_record or admin_record["role"] not in ["admin", "hr"]:
        conn.close()
        raise HTTPException(status_code=403, detail="Unauthorized: Only Admin/HR can register employees.")

    # 2. Duplicate Check
    cursor.execute("SELECT username FROM users WHERE username = ?", (request.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already taken")

    try:
        # Generate Unique ID
        while True:
            new_id = f"user_{random.randint(1000, 9999)}"
            cursor.execute("SELECT user_id FROM employees WHERE user_id = ?", (new_id,))
            if not cursor.fetchone(): break

        # 3. Insert into Employees table
        cursor.execute("""
            INSERT INTO employees (
                user_id, first_name, last_name, email, phone_number,
                position, department, skills, location, hire_date,
                supervisor, salary, available_pto
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_id, request.first_name, request.last_name, request.email,
            request.phone_number, request.position, request.department,
            request.skills, request.location, request.hire_date,
            request.supervisor, request.salary, request.available_pto
        ))

        # 4. Insert into Users table (Storing the hash sent from React)
        cursor.execute("""
            INSERT INTO users (user_id, username, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (new_id, request.username, request.password, request.role))

        conn.commit()
        return {"status": "success", "user_id": new_id, "assigned_role": request.role}

    except Exception as e:
        conn.rollback()
        print(f"Registration Error: {e}")
        raise HTTPException(status_code=500, detail="Database insertion failed.")
    finally:
        conn.close()

@app.get("/health")
def health_check():
    return {"status": "online", "access": "authorized"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)