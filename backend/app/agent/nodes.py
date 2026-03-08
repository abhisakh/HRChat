from langchain_openai import ChatOpenAI
from backend.app.agent.tools.retriever import get_retriever
from backend.app.agent.state import AgentState
from langchain_core.messages import SystemMessage

# Initialize the mini-model (efficient for HR tasks)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def retrieve_node(state: AgentState):
    """
    Step 1: Get the user's question and find relevant docs in Pinecone.
    """
    print("--- NODE: RETRIEVING FROM PINECONE ---")
    # We take the very last message sent by the user
    user_question = state["messages"][-1].content

    retriever = get_retriever()
    # Search Pinecone
    docs = retriever.invoke(user_question)

    # Format the snippets into a list of strings for the state
    context_list = [doc.page_content for doc in docs]

    return {"context": context_list}

def generate_node(state: AgentState):
    """
    Step 2: Use the context + chat history to answer.
    """
    print("--- NODE: GENERATING ANSWER ---")

    # Combine all retrieved snippets into one string
    formatted_context = "\n\n".join(state["context"])
    user_question = state["messages"][-1].content

    # The Prompt: This defines the bot's personality
    system_prompt = f"""You are a helpful and professional HR Assistant.
    Use the following pieces of retrieved context to answer the user's question.
    If the answer isn't in the context, politely say you don't know based on current policies.

    CONTEXT:
    {formatted_context}
    """

    # Create an explicit SystemMessage object
    sys_msg = SystemMessage(content=system_prompt)

    # Combine the lists: [SystemMessage] + [HumanMessage, AIMessage, ...]
    # This ensures every item in the list is a BaseMessage object
    input_messages = [sys_msg] + state["messages"]

    response = llm.invoke(input_messages)

    # Update the 'messages' list (history) and the explicit 'answer' field
    return {
        "messages": [response],
        "answer": response.content
    }