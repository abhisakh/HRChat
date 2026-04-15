#backend/app/agent/nodes.py
import os
import sqlite3
from dotenv import load_dotenv
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from backend.app.agent.state import AgentState
from backend.app.agent.tools.retriever import get_retriever
from backend.app.agent.tools.sql_tool import query_employee_db
from backend.app.db.connection import save_to_audit_log

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# --- HELPER: CONTEXT BUILDER ---
def get_chat_context(messages, limit=5):
    """Formats recent messages into a string for the LLM to understand context."""
    context = ""
    for msg in messages[-limit:]:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        context += f"{role}: {msg.content}\n"
    return context

# --- ROUTER LOGIC ---
# class RouteQuery(BaseModel):
#     """Route a user query to the most appropriate data source."""
#     datasource: Literal["sql", "vector"] = Field(
#         description="Choose 'sql' for personal data/people. Choose 'vector' for general policies."
#     )

class RouteQuery(BaseModel):
    datasource: Literal["sql", "vector"]
    target_entity: str = Field(
        description="The name of the person, a Department (e.g., 'IT', 'HR'), or 'SELF'. Use 'NONE' for general policies."
    )
    reasoning: str = Field(description="Brief explanation of why this path was chosen.")

# def router_node(state: AgentState, config: RunnableConfig):
#     print("--- NODE: ROUTER ---")
#     user_role = config["configurable"].get("role", "employee")

#     # FIX: Provide context so the router knows 'him' refers to a person previously discussed
#     chat_context = get_chat_context(state["messages"])

#     structured_llm = llm.with_structured_output(RouteQuery)

#     route = structured_llm.invoke(
#         f"""
#         User role: {user_role}
#         Recent Conversation:
#         {chat_context}

#         Rules:
#         1. Use 'sql' if the question is about a person, contact info, PTO, salary, or relationships.
#         2. Use 'vector' for company handbooks, dress code, or general 'how-to' policies.
#         3. If the user uses pronouns (him/her/them) regarding a person mentioned in context, use 'sql'.
#         """
#     )

#     return {"source_used": str(route.datasource).lower()}

def router_node(state: AgentState, config: RunnableConfig):
    chat_context = get_chat_context(state["messages"])
    structured_llm = llm.with_structured_output(RouteQuery)

    # We add clear instructions so it knows 'IT' is a valid target for SQL
    instructions = f"""
    Analyze the history and question to determine the target.

    RULES:
    1. If the user asks for a LIST of people in a department (e.g., 'Who works in IT?'),
       set datasource='sql' and target_entity='IT'.
    2. If the user asks about a specific person, set target_entity to their name.
    3. If the user asks about themselves, set target_entity='SELF'.

    History: {chat_context}
    Question: {state['messages'][-1].content}
    """

    result = structured_llm.invoke(instructions)

    return {
        "source_used": result.datasource.lower(),
        "extracted_target": result.target_entity
    }

# --- DATA NODES ---
def retrieve_node(state: AgentState):
    print("--- NODE: VECTOR SEARCH ---")
    user_question = state["messages"][-1].content
    retriever = get_retriever()
    docs = retriever.invoke(user_question)
    return {"context": [doc.page_content for doc in docs]}

# def sql_node(state: AgentState, config: RunnableConfig):
#     """
#         Args:
#         state (AgentState): The current conversation state containing message history.
#         config (RunnableConfig): Runtime configuration including user identity and role.

#     Returns:
#         dict: A dictionary updating the agent state with retrieved SQL context.
#     """

#     print("--- NODE: SQL SEARCH ---")

#     user_id = config["configurable"].get("thread_id", "unknown_user")
#     user_role = config["configurable"].get("role", "employee")

#     # FIX: Send the history context to the SQL tool so it can resolve the 'Target' name
#     chat_context = get_chat_context(state["messages"])

#     result = query_employee_db(user_id, user_role, chat_context)
#     print(f"DEBUG SQL RESULT: {result}")
#     return {"context": [result]}

def sql_node(state: AgentState, config: RunnableConfig):
    user_id = config["configurable"].get("thread_id")
    role = config["configurable"].get("role")

    # Use the target already found by the smart router
    target = state.get("extracted_target", "SELF")

    # Direct DB call, no extra LLM latency!
    result = query_employee_db(user_id, role, target)
    return {"context": [result]}

# --- GENERATION NODE ---
def generate_node(state: AgentState, config: RunnableConfig):
    print("--- NODE: GENERATE ---")

    latest_context = state.get('context', 'No data found.')

    # Check if the context is a list (multiple employees found)
    context_str = str(latest_context)

    prompt_text = f"""
    You are the Umbrella Corp HR System.

    DATA RETRIEVED:
    {latest_context}

    USER ROLE: {config["configurable"].get("role")}

    INSTRUCTIONS:
    1. If the DATA RETRIEVED contains the person's info, answer the question directly.
    2. If the user asks for 'Salary' and the field is missing from the data, explain: "Access Denied: Your security clearance level ({config["configurable"].get("role")}) does not permit viewing salary information for other personnel."
    3. Do not say "I couldn't find it" if the person is in the database but the specific field is missing—be honest about the restriction.
    """

    messages = [
        SystemMessage(content=prompt_text),
        *state["messages"][-5:]
    ]

    response = llm.invoke(messages)
    return {"answer": response.content}

# --- AUDIT NODE ---
def audit_node(state: AgentState, config: RunnableConfig):
    print("--- NODE: AUDIT LOGGING ---")

    user_id = config["configurable"].get("thread_id", "unknown_user")
    source = state.get("source_used", "vector")

    # The actual question is the last message in the state
    user_question = state["messages"][-1].content if state["messages"] else "Unknown"
    current_path = f"router -> {source}_search -> generate"

    save_to_audit_log(
        user_id=user_id,
        question=user_question,
        answer=state["answer"],
        source=source,
        node_path=current_path
    )

    return state