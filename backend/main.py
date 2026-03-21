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
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path

# Import the graph and the DB initialization
from backend.app.agent.graph import hr_agent
from backend.app.db.connection import init_db
from langchain_core.messages import HumanMessage

# Path to your database
DB_PATH = Path(__file__).parent / "app" / "db" / "hr_database.db"

app = FastAPI(
    title="HRChat API",
    description="Multi-user HR Assistant with Persistent Hybrid RAG",
    version="1.2.0"
)

# --- 1. Database Initialization on Startup ---
@app.on_event("startup")
async def startup_event():
    init_db()

# --- 2. Request/Response Models ---
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

# --- 3. Authentication Helper ---
def verify_user(username, password):
    """Checks the database for matching username and hashed password."""
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id FROM users WHERE username = ? AND password_hash = ?",
        (username, password_hash)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# --- 4. The Login Endpoint ---
@app.post("/login")
async def login(request: LoginRequest):
    user_id = verify_user(request.username, request.password)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # In the future, you'd return a JWT token here
    return {"user_id": user_id, "status": "success"}

# --- 5. The Chat Endpoint ---
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        config = {"configurable": {"thread_id": request.user_id}}
        initial_state = {"messages": [HumanMessage(content=request.message)]}

        final_state = hr_agent.invoke(initial_state, config=config)

        return ChatResponse(
            user_id=request.user_id,
            answer=final_state["answer"],
            source=final_state.get("source_used", "unknown")
        )
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- 6. Health Check ---
@app.get("/health")
def health_check():
    return {"status": "online", "model": "gpt-4o-mini"}

# --- 7. Adding a new user ---------
class RegisterRequest(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    position: str
    salary: float

@app.post("/register")
async def register(request: RegisterRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Check if username exists
    cursor.execute("SELECT username FROM users WHERE username = ?", (request.username,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Username already taken")

    try:
        # 2. Generate a new User ID
        new_id = f"user_{random.randint(1000, 9999)}"

        # 3. Insert into Employees (The AI's data source)
        cursor.execute("""
            INSERT INTO employees (user_id, first_name, last_name, position, salary)
            VALUES (?, ?, ?, ?, ?)
        """, (new_id, request.first_name, request.last_name, request.position, request.salary))

        # 4. Insert into Users (The Security source)
        password_hash = hashlib.sha256(request.password.encode()).hexdigest()
        cursor.execute("""
            INSERT INTO users (user_id, username, password_hash)
            VALUES (?, ?, ?)
        """, (new_id, request.username, password_hash))

        conn.commit()
        return {"status": "success", "user_id": new_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# --- Admin Deleting User ---
class DeleteRequest(BaseModel):
    user_id: str  # We delete by ID for precision

@app.post("/delete_user")
async def delete_user(request: DeleteRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if user exists first
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (request.user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        # Start a transaction to ensure both are deleted or none are
        cursor.execute("DELETE FROM users WHERE user_id = ?", (request.user_id,))
        cursor.execute("DELETE FROM employees WHERE user_id = ?", (request.user_id,))
        # Optional: Clear their chat history/audit logs too
        cursor.execute("DELETE FROM chat_audit_logs WHERE user_id = ?", (request.user_id,))

        conn.commit()
        return {"status": "success", "message": f"User {request.user_id} offboarded successfully."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


