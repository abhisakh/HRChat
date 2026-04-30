from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import os

from backend.app.agent.state import AgentState
from backend.app.agent.nodes import (
    router_node,
    retrieve_node,
    sql_node,
    generate_node,
    audit_node
)

# ============================================================
# 1. Initialize Graph
# ============================================================
builder = StateGraph(AgentState)

# ============================================================
# 2. Add Nodes
# ============================================================
builder.add_node("router", router_node)
builder.add_node("retrieve", retrieve_node)
builder.add_node("sql_search", sql_node)
builder.add_node("generate", generate_node)
builder.add_node("audit", audit_node)

# ============================================================
# 3. Start Flow
# ============================================================
builder.add_edge(START, "router")

# ============================================================
# 4. SAFE ROUTING (HARDENED)
# ============================================================
def safe_router(state):
    route = state.get("source_used", "sql")

    if not route:
        return "sql_search"

    route = str(route).lower().strip()

    if route in ["sql", "sql_search"]:
        return "sql_search"

    if route in ["vector", "retrieve", "search"]:
        return "retrieve"

    # fallback (VERY IMPORTANT for autotests)
    return "sql_search"


builder.add_conditional_edges(
    "router",
    safe_router,
    {
        "sql_search": "sql_search",
        "retrieve": "retrieve"
    }
)

# ============================================================
# 5. Flow Continuation
# ============================================================
builder.add_edge("sql_search", "generate")
builder.add_edge("retrieve", "generate")

builder.add_edge("generate", "audit")
builder.add_edge("audit", END)

# ============================================================
# 6. Safe Checkpointer Setup
# ============================================================
DB_DIR = os.path.join("backend", "app", "db")
os.makedirs(DB_DIR, exist_ok=True)

conn = sqlite3.connect(
    os.path.join(DB_DIR, "checkpoints.sqlite"),
    check_same_thread=False
)

memory = SqliteSaver(conn)

# ============================================================
# 7. Compile Agent
# ============================================================
hr_agent = builder.compile(checkpointer=memory)




# from langgraph.graph import StateGraph, START, END
# from langgraph.checkpoint.sqlite import SqliteSaver # New for 2026
# import sqlite3

# from backend.app.agent.state import AgentState
# from backend.app.agent.nodes import (
#     router_node,
#     retrieve_node,
#     sql_node,
#     generate_node,
#     audit_node
# )

# # 1. Initialize the Graph
# builder = StateGraph(AgentState)

# # 2. Add all your Nodes
# builder.add_node("router", router_node)
# builder.add_node("retrieve", retrieve_node)
# builder.add_node("sql_search", sql_node)
# builder.add_node("generate", generate_node)
# builder.add_node("audit", audit_node)

# # 3. Define the Flow
# builder.add_edge(START, "router")

# # --- THE CONDITIONAL EDGE ---
# # This looks at 'source_used' in the state and picks the next node
# builder.add_conditional_edges(
#     "router",
#     lambda state: str(state.get("source_used", "vector")).lower().strip(),
#     {
#         "sql": "sql_search",
#         "vector": "retrieve"
#     }
# )

# # Both paths converge back to generation
# builder.add_edge("sql_search", "generate")
# builder.add_edge("retrieve", "generate")

# # Final step: Audit then finish
# builder.add_edge("generate", "audit")
# builder.add_edge("audit", END)

# # 4. Persistence (Short-term Memory)
# # We use a context manager to ensure the DB connection stays open
# conn = sqlite3.connect("backend/app/db/checkpoints.sqlite", check_same_thread=False)
# memory = SqliteSaver(conn)

# # 5. Compile
# hr_agent = builder.compile(checkpointer=memory)