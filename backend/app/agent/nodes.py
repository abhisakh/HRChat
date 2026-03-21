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

def router_node(state: AgentState):
    """Analyzes the question to decide between SQL and Vector."""
    print("--- NODE: ROUTER ---")
    structured_llm = llm.with_structured_output(RouteQuery)
    user_question = state["messages"][-1].content

    route = structured_llm.invoke(f"Analyze this HR question: {user_question}")
    return {"source_used": route.datasource}

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
    # We pull the thread_id (user_id) directly from the config
    user_id = config["configurable"].get("thread_id", "unknown_user")
    user_question = state["messages"][-1].content

    # We use our tool to query the employee table
    result = query_employee_db(user_id, user_question)
    return {"context": [result]}

# --- GENERATION NODE ---
def generate_node(state: AgentState):
    """Generates the final response based on the gathered context."""
    print("--- NODE: GENERATE ---")
    formatted_context = "\n\n".join(state["context"])

    system_prompt = f"""You are a professional HR Assistant.
    Use the retrieved context to answer. If the context is from a database, treat it as fact.
    CONTEXT: {formatted_context}"""

    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm.invoke(messages)

    return {"messages": [response], "answer": response.content}

# --- AUDIT NODE ---
def audit_node(state: AgentState, config: RunnableConfig):
    """Final node to record the transaction."""
    print("--- NODE: AUDIT LOGGING ---")

    # Extract details from the state and config
    user_id = config["configurable"].get("thread_id", "unknown_user")
    # messages[0] is usually the very first HumanMessage in the thread
    # messages[-2] is the most recent HumanMessage if history is long
    user_question = state["messages"][-2].content if len(state["messages"]) > 1 else "Unknown"

    save_to_audit_log(
        user_id=user_id,
        question=user_question,
        answer=state["answer"],
        source=state.get("source_used", "vector")
    )

    return state