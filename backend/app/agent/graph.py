from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from backend.app.agent.state import AgentState
from backend.app.agent.nodes import retrieve_node, generate_node

# 1. Initialize the Graph
builder = StateGraph(AgentState)

# 2. Define the Nodes
builder.add_node("retrieve", retrieve_node)
builder.add_node("generate", generate_node)

# 3. Connect the Nodes
builder.add_edge(START, "retrieve")    # Start -> Retrieve
builder.add_edge("retrieve", "generate") # Retrieve -> Generate
builder.add_edge("generate", END)        # Generate -> End

# 4. Enable Memory (Isolation per user account)
# MemorySaver keeps track of messages per 'thread_id'
checkpointer = MemorySaver()

# 5. Compile the Graph
hr_agent = builder.compile(checkpointer=checkpointer)