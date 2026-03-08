import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

# Import the graph we compiled earlier
from backend.app.agent.graph import hr_agent
from langchain_core.messages import HumanMessage

app = FastAPI(
    title="HRChat API",
    description="Multi-user HR Assistant with Persistent RAG Memory",
    version="1.0.0"
)

# --- 1. Request/Response Models ---
class ChatRequest(BaseModel):
    # This matches your 'separate accounts' requirement.
    # Use a unique ID for each user or session.
    user_id: str = Field(..., example="user_88")
    message: str = Field(..., example="How many days of PTO do I get?")

class ChatResponse(BaseModel):
    user_id: str
    answer: str

# --- 2. The Chat Endpoint ---
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Config used by LangGraph's MemorySaver
        # Everything under 'thread_id' belongs to one specific 'user_id'
        config = {"configurable": {"thread_id": request.user_id}}

        # Prepare the input for the graph
        initial_state = {
            "messages": [HumanMessage(content=request.message)]
        }

        # Invoke the graph. It will automatically:
        # 1. Retrieve history for this thread_id
        # 2. Run retrieve_node -> generate_node
        # 3. Save the new state back to memory
        final_state = hr_agent.invoke(initial_state, config=config)

        return ChatResponse(
            user_id=request.user_id,
            answer=final_state["answer"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 3. Health Check ---
@app.get("/health")
def health_check():
    return {"status": "online", "model": "gpt-4o-mini"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)