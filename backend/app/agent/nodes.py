import os
import sqlite3
from dotenv import load_dotenv
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig # NEW: To access thread_id

from backend.app.agent.state import AgentState
from backend.app.agent.tools.retriever import get_retriever
from backend.app.agent.tools.sql_tool import query_employee_db
from backend.app.db.connection import save_to_audit_log
# Load the .env file
load_dotenv()

# Initialize the model
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY") # This is what you were referring to
)

# --- ROUTER LOGIC ---
class RouteQuery(BaseModel):
    """Route a user query to the most appropriate data source."""
    datasource: Literal["sql", "vector"] = Field(
        description="Choose 'sql' for personal data like PTO, salary, or employee records. Choose 'vector' for general HR policies, handbooks, and dress codes."
    )

def router_node(state: AgentState, config: RunnableConfig):
    print("--- NODE: ROUTER ---")
    user_role = config["configurable"].get("role", "employee")
    user_question = state["messages"][-1].content

    structured_llm = llm.with_structured_output(RouteQuery)

    # Improved prompt to differentiate between "Policy" and "Data"
    route = structured_llm.invoke(
        f"""
        User role: {user_role}
        Question: {user_question}

        Strict Routing Rules:
        1. Use 'sql' if the question requires looking up a specific person, a specific balance (PTO/Salary), or a direct relationship (Supervisor/Team).
        2. Use 'vector' ONLY for general rules, 'how-to' guides, or company-wide policies that apply to everyone.

        If the question is about 'Who', 'My', or 'Me', always choose 'sql'.
        """
    )

    return {"source_used": str(route.datasource).lower()} # Force lowercase for the Edge match

# --- DATA NODES ---
def retrieve_node(state: AgentState):
    """Fetches general policy data from Pinecone."""
    print("--- NODE: VECTOR SEARCH ---")
    user_question = state["messages"][-1].content
    retriever = get_retriever()
    docs = retriever.invoke(user_question)
    return {"context": [doc.page_content for doc in docs]}

def sql_node(state: AgentState, config: RunnableConfig):
    """Fetches structured personal data from SQLite."""
    print("--- NODE: SQL SEARCH ---")

    user_id = config["configurable"].get("thread_id", "unknown_user")
    user_role = config["configurable"].get("role", "employee")
    user_question = state["messages"][-1].content

    # 🔐 Pass role into SQL tool
    result = query_employee_db(user_id, user_role, user_question)
    print(f"DEBUG SQL RESULT: {result}")
    return {"context": [result]}

# --- GENERATION NODE ---
def generate_node(state: AgentState, config: RunnableConfig):
    print("--- NODE: GENERATE ---")

    # DEFINE the prompt first!
    prompt_text = f"""
    You are a helpful HR Assistant.
    Context from Database: {state['context']}

    Answer the user's question based ONLY on the context provided.
    If contact info is there, share it. If salary is missing, say it's restricted.
    """

    # Ensure you are calling the LLM with the defined string
    messages = [
        {"role": "system", "content": prompt_text},
        {"role": "user", "content": state["messages"][-1].content}
    ]

    response = llm.invoke(messages)
    return {"answer": response.content}

# --- AUDIT NODE ---
def audit_node(state: AgentState, config: RunnableConfig):
    """Final node to record the transaction."""
    print("--- NODE: AUDIT LOGGING ---")

    # 1. Extract details
    user_id = config["configurable"].get("thread_id", "unknown_user")
    source = state.get("source_used", "vector")

    # Get the user's question (usually the second to last message in the list)
    user_question = state["messages"][-2].content if len(state["messages"]) > 1 else "Unknown"

    # 2. CREATE the missing argument
    # This helps you track the AI's logic path in your database
    current_path = f"router -> {source}_search -> generate"

    # 3. Call with all 5 arguments
    save_to_audit_log(
        user_id=user_id,
        question=user_question,
        answer=state["answer"],
        source=source,
        node_path=current_path  # <--- FIXED: Added the missing 5th argument
    )

    return state