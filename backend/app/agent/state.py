from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # 'messages' will store the full chat history (User and AI messages)
    # Annotated with add_messages so new messages are appended, not overwritten.
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # 'context' will hold the snippets retrieved from Pinecone
    context: list[str]

    # 'answer' stores the final generated response
    answer: str