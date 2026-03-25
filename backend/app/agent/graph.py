from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver # New for 2026
import sqlite3

from backend.app.agent.state import AgentState
from backend.app.agent.nodes import (
    router_node,
    retrieve_node,
    sql_node,
    generate_node,
    audit_node
)

# 1. Initialize the Graph
builder = StateGraph(AgentState)

# 2. Add all your Nodes
builder.add_node("router", router_node)
builder.add_node("retrieve", retrieve_node)
builder.add_node("sql_search", sql_node)
builder.add_node("generate", generate_node)
builder.add_node("audit", audit_node)

# 3. Define the Flow
builder.add_edge(START, "router")

# --- THE CONDITIONAL EDGE ---
# This looks at 'source_used' in the state and picks the next node
builder.add_conditional_edges(
    "router",
    lambda state: str(state.get("source_used", "vector")).lower().strip(),
    {
        "sql": "sql_search",
        "vector": "retrieve"
    }
)

# Both paths converge back to generation
builder.add_edge("sql_search", "generate")
builder.add_edge("retrieve", "generate")

# Final step: Audit then finish
builder.add_edge("generate", "audit")
builder.add_edge("audit", END)

# 4. Persistence (Short-term Memory)
# We use a context manager to ensure the DB connection stays open
conn = sqlite3.connect("backend/app/db/checkpoints.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)

# 5. Compile
hr_agent = builder.compile(checkpointer=memory)