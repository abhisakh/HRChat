# import uvicorn
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel, Field

# # Import the graph and the DB initialization
# from backend.app.agent.graph import hr_agent
# from backend.app.db.connection import init_db
# from langchain_core.messages import HumanMessage

# app = FastAPI(
#     title="HRChat API",
#     description="Multi-user HR Assistant with Persistent Hybrid RAG",
#     version="1.1.0"
# )

# # --- 1. Database Initialization on Startup ---
# @app.on_event("startup")
# async def startup_event():
#     """Ensure all SQL tables exist before the first request arrives."""
#     print("Initializing HR Databases...")
#     init_db()

# # --- 2. Request/Response Models ---
# class ChatRequest(BaseModel):
#     user_id: str = Field(..., example="user_88")
#     message: str = Field(..., example="How many vacation days do I have?")

# class ChatResponse(BaseModel):
#     user_id: str
#     answer: str
#     source: str # Added so the UI knows if it came from SQL or PDF

# # --- 3. The Chat Endpoint ---
# @app.post("/chat", response_model=ChatResponse)
# async def chat_endpoint(request: ChatRequest):
#     try:
#         # thread_id ensures User A doesn't see User B's chat history
#         config = {"configurable": {"thread_id": request.user_id}}

#         # We pass the message AND the user_id into the graph state
#         initial_state = {
#             "messages": [HumanMessage(content=request.message)]
#         }

#         # Invoke the Hybrid Graph
#         final_state = hr_agent.invoke(initial_state, config=config)

#         return ChatResponse(
#             user_id=request.user_id,
#             answer=final_state["answer"],
#             source=final_state.get("source_used", "unknown")
#         )

#     except Exception as e:
#         print(f"Error: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")

# # --- 4. Health Check ---
# @app.get("/health")
# def health_check():
#     return {"status": "online", "model": "gpt-4o-mini"}

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)

import uvicorn
import sqlite3
import hashlib
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
from typing import List, Optional

from backend.app.agent.graph import hr_agent
from backend.app.db.connection import init_db, save_to_audit_log
from langchain_core.messages import HumanMessage
from fastapi.middleware.cors import CORSMiddleware

# --- 0. Configuration ---
DB_PATH = Path(__file__).parent / "app" / "db" / "hr_database.db"

app = FastAPI(
    title="HRChat API",
    description="Multi-user HR Assistant with RBAC",
    version="2.1.0"
)

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
    init_db()

# --- 2. Models ---
class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    user_id: str
    answer: str
    source: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    position: str
    salary: float

class DeleteRequest(BaseModel):
    user_id: str

# --- 3. DB Helpers ---
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Crucial for accessing columns by name
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def verify_user(username, password):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT u.user_id, u.role, e.first_name
        FROM users u
        JOIN employees e ON u.user_id = e.user_id
        WHERE u.username = ? AND u.password_hash = ?
    """
    cursor.execute(query, (username, password_hash))
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
    """Retrieves and flattens history from chat_audit_logs for the Chat UI."""
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
    except sqlite3.OperationalError:
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
        user_role = get_user_role(request.user_id)
        config = {"configurable": {"thread_id": request.user_id, "role": user_role}}
        initial_state = {"messages": [HumanMessage(content=request.message)]}

        final_state = hr_agent.invoke(initial_state, config=config)

        # Save to your existing audit table
        save_to_audit_log(
            user_id=request.user_id,
            question=request.message,
            answer=final_state["answer"],
            source=final_state.get("source_used", "unknown"),
            node_path=" -> ".join(final_state.get("steps", ["start", "end"]))
        )

        return ChatResponse(
            user_id=request.user_id,
            answer=final_state["answer"],
            source=final_state.get("source_used", "unknown")
        )
    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/chat/history/{user_id}")
async def chat_history(user_id: str):
    history = get_memory_by_user(user_id)
    return {"history": history}

@app.get("/audit/logs/{user_id}")
async def audit_logs(user_id: str):
    """Detailed logs for the 'Audit Logs' tab in React."""
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

@app.post("/register")
async def register(request: RegisterRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username = ?", (request.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already taken")

    try:
        new_id = f"user_{random.randint(1000, 9999)}"
        role = "hr" if "hr" in request.position.lower() else "employee"

        cursor.execute("""
            INSERT INTO employees (user_id, first_name, last_name, position, salary)
            VALUES (?, ?, ?, ?, ?)
        """, (new_id, request.first_name, request.last_name, request.position, request.salary))

        password_hash = hashlib.sha256(request.password.encode()).hexdigest()
        cursor.execute("""
            INSERT INTO users (user_id, username, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (new_id, request.username, password_hash, role))

        conn.commit()
        return {"status": "success", "user_id": new_id, "role": role}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/health")
def health_check():
    return {"status": "online"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)