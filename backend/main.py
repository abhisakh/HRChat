#backend/main.py
import uvicorn
import sqlite3
import hashlib
import random
import bcrypt
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
    phone_number: Optional[str] = None
    position: str
    department: str
    location: Optional[str] = None
    hire_date: str
    supervisor_id: Optional[str] = None
    skills: Optional[str] = None
    salary: float
    role: str = "employee"
    available_pto: int = 15


# --- 3. DB Helpers ---

def get_connection():
    # Adding a 20-second timeout to wait for locks to clear
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # This mode is much better for concurrent access (Read/Write)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def verify_user(username, password):
    print("\n---- RAW INPUT DEBUG ----")
    print(f"username repr: {repr(username)}")
    print(f"password repr: {repr(password)}")
    print(f"password length: {len(password) if password else 0}")
    print("-------------------------")
    # 1. Clean the inputs immediately
    u = username.strip()
    p = password.strip()

    # 2. Generate the hash from the CLEANED password
    incoming_hash = hashlib.sha256(p.encode('utf-8')).hexdigest()

    print(f"\n--- [AUTH DEBUG START] ---")
    print(f"Login Attempt Username: '{u}'")
    print(f"Generated Hash: {incoming_hash}")

    conn = get_connection()
    cursor = conn.cursor()

    # 3. Use the CLEANED username to look up the user
    cursor.execute("SELECT username, password_hash FROM users WHERE username = ?", (u,))
    db_user = cursor.fetchone()

    if not db_user:
        print(f"Result: USER NOT FOUND.")
        conn.close()
        return None

    print(f"Database Hash Found: {db_user['password_hash']}")

    if db_user['password_hash'] != incoming_hash:
        print("Result: HASH MISMATCH.")
        conn.close()
        return None

    # 4. Final Join Check
    query = """
        SELECT u.user_id, u.role, e.first_name
        FROM users u
        JOIN employees e ON u.user_id = e.user_id
        WHERE u.username = ? AND u.password_hash = ?
    """
    cursor.execute(query, (u, incoming_hash))
    result = cursor.fetchone()
    conn.close()

    if result:
        print("Result: SUCCESS.")
        # Access by index to be safe (0: user_id, 1: role, 2: first_name)
        return {
            "user_id": result[0],
            "role": result[1],
            "first_name": result[2]
        }

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

# @app.post("/chat", response_model=ChatResponse)
# async def chat_endpoint(request: ChatRequest):
#     try:
#         # 1. Validate User & Role
#         user_role = get_user_role(request.user_id)
#         if not user_role:
#             raise HTTPException(status_code=403, detail="User role not found.")

#         # 2. Context Restoration & Deduplication Logic
#         # If frontend history is empty (e.g., refresh/re-login), pull from DB
#         effective_history = request.history
#         if not effective_history or len(effective_history) == 0:
#             raw_db_history = get_memory_by_user(request.user_id)
#             effective_history = [
#                 ChatMessage(role=m["role"], content=m["content"])
#                 for m in raw_db_history[-10:] # Last 10 messages for context
#             ]

#         # 3. Convert to LangChain Format
#         formatted_messages = []
#         for msg in effective_history:
#             if msg.role.lower() in ["user", "human"]:
#                 formatted_messages.append(HumanMessage(content=msg.content))
#             else:
#                 formatted_messages.append(AIMessage(content=msg.content))

#         # Add the current user query
#         formatted_messages.append(HumanMessage(content=request.message))

#         # 4. State Management & Invocation
#         # We use a unique thread_id.
#         # To avoid duplication with LangGraph's internal SqliteSaver:
#         # We pass the full history into the 'messages' key.
#         config = {"configurable": {"thread_id": request.user_id, "role": user_role}}

#         # We 'update' the state explicitly to ensure the graph uses our curated list
#         initial_state = {"messages": formatted_messages}

#         # Invoke the Agent
#         final_state = hr_agent.invoke(initial_state, config=config)

#         # 5. Safety Check for Missing Data
#         answer = final_state.get("answer", "I'm sorry, I encountered an error generating a response.")
#         source = final_state.get("source_used", "unknown")
#         # Ensure node_path is a list before joining
#         steps = final_state.get("steps", ["start", "process", "end"])
#         path_str = " -> ".join(steps) if isinstance(steps, list) else str(steps)

#         # 6. Final Audit & Response
#         save_to_audit_log(
#             user_id=request.user_id,
#             question=request.message,
#             answer=answer,
#             source=source,
#             node_path=path_str
#         )

#         return ChatResponse(
#             user_id=request.user_id,
#             answer=answer,
#             source=source
#         )

#     except Exception as e:
#         # Log the actual error to console for debugging
#         print(f"--- [CRITICAL ERROR] --- \nType: {type(e).__name__} \nDetail: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # 1. Validate User & Role
        user_role = get_user_role(request.user_id)
        if not user_role:
            raise HTTPException(status_code=403, detail="User role not found.")

        # 2. Simplified State Management
        # LangGraph's SqliteSaver handles history automatically using thread_id.
        # We ONLY send the latest human message.
        config = {"configurable": {"thread_id": request.user_id, "role": user_role}}

        # We pass ONLY the new message.
        # The checkpointer will merge this with existing history.
        new_input = {"messages": [HumanMessage(content=request.message)]}

        # 3. Invoke the Agent
        final_state = hr_agent.invoke(new_input, config=config)

        # 4. Extract Response Data
        answer = final_state.get("answer", "I encountered an error.")
        source = final_state.get("source_used", "unknown")
        steps = final_state.get("steps", [])
        path_str = " -> ".join(steps) if isinstance(steps, list) else str(steps)

        # # 5. Audit Logging
        # save_to_audit_log(
        #     user_id=request.user_id,
        #     question=request.message,
        #     answer=answer,
        #     source=source,
        #     node_path=path_str
        # )

        return ChatResponse(
            user_id=request.user_id,
            answer=answer,
            source=source
        )

    except Exception as e:
        print(f"--- [ERROR] --- {e}")
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

    print("\n========== REGISTER START ==========")
    print(f"[DEBUG] admin_id: {request.admin_id}")
    print(f"[DEBUG] username: {request.username}")
    print(f"[DEBUG] supervisor_id: {request.supervisor_id}")

    try:
        # =========================================================
        # 1. AUTH CHECK
        # =========================================================
        cursor.execute(
            "SELECT role FROM users WHERE user_id = ?",
            (request.admin_id,)
        )
        admin_record = cursor.fetchone()

        print(f"[DEBUG] admin_record: {admin_record}")

        if not admin_record or admin_record["role"] not in ["admin", "hr"]:
            print("[DEBUG] AUTH FAILED")
            raise HTTPException(
                status_code=403,
                detail="Unauthorized: Only Admin/HR can register personnel."
            )

        # =========================================================
        # 2. DUPLICATE USERNAME CHECK
        # =========================================================
        cursor.execute(
            "SELECT username FROM users WHERE username = ?",
            (request.username,)
        )
        duplicate = cursor.fetchone()

        print(f"[DEBUG] duplicate username check: {duplicate}")

        if duplicate:
            raise HTTPException(
                status_code=400,
                detail="Username already exists."
            )

        # =========================================================
        # 3. GENERATE USER ID
        # =========================================================
        while True:
            new_id = f"user_{random.randint(1000, 9999)}"
            cursor.execute(
                "SELECT user_id FROM users WHERE user_id = ?",
                (new_id,)
            )
            exists = cursor.fetchone()
            print(f"[DEBUG] trying user_id={new_id}, exists={exists}")
            if not exists:
                break

        print(f"[DEBUG] FINAL new_id: {new_id}")

        # =========================================================
        # 4. NORMALIZE SUPERVISOR ID
        # =========================================================
        supervisor_id = request.supervisor_id
        print(f"SUPERVISOR REQUESTED: {supervisor_id }")
        print("[DEBUG] supervisor_id FINAL TYPE:", type(supervisor_id), supervisor_id)
        if not supervisor_id or str(supervisor_id).strip() == "":
            supervisor_id = None
        else:
            cursor.execute(
                "SELECT user_id FROM employees WHERE user_id = ?",
                (supervisor_id,)
            )
            sup = cursor.fetchone()

            print(f"[DEBUG] supervisor lookup result: {sup}")

            if not sup:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid supervisor_id."
                )

        # =========================================================
        # 5. HASH PASSWORD
        # =========================================================
        password_hash = hashlib.sha256(
            request.password.encode("utf-8")
        ).hexdigest()

        print(f"[DEBUG] password hashed OK")

        # =========================================================
        # 6. INSERT USERS
        # =========================================================
        print("[DEBUG] inserting into USERS...")

        cursor.execute("""
            INSERT INTO users (
                user_id,
                username,
                password_hash,
                role
            )
            VALUES (?, ?, ?, ?)
        """, (
            new_id,
            request.username,
            password_hash,
            request.role
        ))

        print("[DEBUG] USERS insert done")

        # =========================================================
        # 7. INSERT EMPLOYEE
        # =========================================================
        print("[DEBUG] inserting into EMPLOYEES...")

        cursor.execute("""
            INSERT INTO employees (
                user_id,
                first_name,
                last_name,
                email,
                phone_number,
                position,
                department,
                location,
                hire_date,
                supervisor_id,
                salary,
                available_pto
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_id,
            request.first_name,
            request.last_name,
            request.email,
            request.phone_number,
            request.position,
            request.department,
            request.location,
            request.hire_date,
            supervisor_id,
            request.salary,
            request.available_pto
        ))

        print("[DEBUG] EMPLOYEES insert done")

        # =========================================================
        # 8. INSERT SKILLS
        # =========================================================
        if request.skills:
            skill_list = [
                s.strip().lower()
                for s in request.skills.split(",")
                if s.strip()
            ]

            print(f"[DEBUG] skills: {skill_list}")

            for skill in skill_list:
                cursor.execute("""
                    INSERT INTO employee_skills (user_id, skill)
                    VALUES (?, ?)
                """, (new_id, skill))

        # =========================================================
        # 9. COMMIT
        # =========================================================
        conn.commit()

        print("[DEBUG] COMMIT SUCCESS")
        print("========== REGISTER END ==========\n")

        return {
            "status": "success",
            "user_id": new_id,
            "assigned_role": request.role
        }

    except HTTPException:
        conn.rollback()
        print("[DEBUG] HTTPException rollback")
        raise

    except Exception as e:
        conn.rollback()
        print(f"--- [ERROR] REGISTER FAILED --- {e}")
        raise HTTPException(
            status_code=500,
            detail="Database provisioning failed."
        )

    finally:
        conn.close()

@app.get("/health")
def health_check():
    return {"status": "online", "access": "authorized"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)