# backend/app/agent/nodes.py

import os
import re
import json
from dotenv import load_dotenv
from typing import Literal
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from backend.app.agent.state import AgentState
from backend.app.agent.tools.retriever import get_retriever
from backend.app.agent.tools.sql_tool import query_employee_db
from backend.app.db.connection import save_to_audit_log

load_dotenv()

# ---------------- LLM ----------------
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

# ---------------- ROUTER SCHEMA ----------------
class RouteQuery(BaseModel):
    datasource: Literal["sql", "vector"]
    target_entity: str = Field(
        description="Person name, department, SELF, or NONE"
    )
    reasoning: str = Field(description="Why this route was chosen")


# ---------------- HELPERS ----------------
def summarize_text(text: str) -> str:
    """Lemon-simple conversation compression."""
    response = llm.invoke([
        SystemMessage(content="Summarize the following conversation briefly in simple words."),
        HumanMessage(content=text)
    ])
    return response.content

def get_chat_context(messages, limit=10):
    context = ""
    for msg in messages[-limit:]:
        role = "User" if msg.type == "human" else "Assistant"
        context += f"{role}: {msg.content}\n"
    return context


# ============================================================
# ROUTER NODE
# ============================================================
def router_node(state: AgentState, config: RunnableConfig):
    print("--- NODE: ROUTER ---")

    chat_history_text = get_chat_context(state["messages"])
    summary = summarize_text(chat_history_text)

    structured_llm = llm.with_structured_output(RouteQuery)

    instructions = f"""
    Decide routing for HR query.
    - sql: employee details, salary, department lists, contact info.
    - vector: company policies, handbook, general rules.

    HISTORY SUMMARY: {summary}
    CURRENT QUESTION: {state['messages'][-1].content}
    """

    result = structured_llm.invoke(instructions)
    print(f" User Query: {state['messages'][-1].content}")

    return {
        "source_used": result.datasource,
        "extracted_target": result.target_entity,
        "steps": state.get("steps", []) + ["router"]
    }


# ============================================================
# VECTOR SEARCH NODE
# ============================================================
def retrieve_node(state: AgentState):
    print("--- NODE: VECTOR SEARCH ---")

    query = state["messages"][-1].content
    retriever = get_retriever()
    docs = retriever.invoke(query)

    # Return list of text snippets
    return {"context": [d.page_content for d in docs]}


# ============================================================
# SQL NODE
# ============================================================
def sql_node(state: AgentState, config: RunnableConfig):
    print("\n" + "="*30)
    print("--- NODE: SQL SEARCH ---")
    user_id = config["configurable"].get("thread_id")
    role = config["configurable"].get("role")
    target = state.get("extracted_target", "SELF")

    print(f"[DEBUG] Target: {target} | Role: {role} | UserID: {user_id}")

    # Call DB
    result = query_employee_db(user_id, role, target)
    print(f"[DEBUG] DB Raw Result Type: {type(result)}")
    print(f"[DEBUG] DB Raw Content: {result}")

    # Convert to JSON string for state compatibility (list[str])
    if isinstance(result, (dict, list)):
        context_string = json.dumps(result)
        print(f"[DEBUG] Serialized dict/list to JSON string.")
    else:
        context_string = str(result)
        print(f"[DEBUG] Result was already string/error.")

    print(f"[DEBUG] Final Context to State: {context_string[:100]}...")
    print("="*30 + "\n")

    return {"context": [context_string]}

# ============================================================
# GENERATE NODE (Schema-Aware + Secure PII Sandwich + Intent Aware)
# ============================================================
def generate_node(state: AgentState, config: RunnableConfig):
    print("\n" + "="*30)
    print("--- NODE: GENERATE ---")

    raw_context = state.get("context", [])
    source = state.get("source_used", "sql")
    role = config["configurable"].get("role", "User")

    print(f"[DEBUG] Source Used: {source}")
    print(f"[DEBUG] Raw Context from State: {raw_context}")

    # ============================================================
    # 1. Parse Context Safely
    # ============================================================
    try:
        parsed = json.loads(raw_context[0]) if raw_context else {}
        raw_data = parsed.get("data", parsed)
        status = parsed.get("status")
        print(f"[DEBUG] Parsed JSON successfully. Type: {type(raw_data)}")
    except (json.JSONDecodeError, TypeError, IndexError):
        raw_data = raw_context[0] if raw_context else "No data found."
        status = None
        print(f"[DEBUG] Fallback parsing used. Type: {type(raw_data)}")

    # ============================================================
    # 1.5 Handle DB Errors Early (IMPORTANT)
    # ============================================================
    if isinstance(parsed, dict) and parsed.get("status") == "error":
        return {
            "answer": f"System error: {parsed.get('message')}. Please contact admin."
        }

    # ============================================================
    # 2. Detect Data Type
    # ============================================================
    is_direct_msg = isinstance(raw_data, str)
    data_keys = []

    if not is_direct_msg:
        sample = raw_data[0] if isinstance(raw_data, list) else raw_data
        if isinstance(sample, dict):
            data_keys = list(sample.keys())

    print(f"[DEBUG] Is Direct Message: {is_direct_msg}")
    print(f"[DEBUG] Data Keys: {data_keys}")

    # ============================================================
    # 3. PRE-LMM LOGIC (SECURITY + INTENT + TARGET)
    # ============================================================
    user_query = state["messages"][-1].content.lower()
    target = state.get("target", "").lower()

    contact_keywords = ["contact", "email", "phone", "reach"]
    is_contact_query = any(k in user_query for k in contact_keywords)

    if source == "sql" and isinstance(raw_data, (list, dict)):
        records = raw_data if isinstance(raw_data, list) else [raw_data]

        processed_records = []

        for r in records:
            if not isinstance(r, dict):
                continue

            # 🔒 Remove supervisor data unless explicitly requested
            if not any(k in user_query for k in ["manager", "supervisor", "reports"]):
                r.pop("supervisor_name", None)
                r.pop("supervisor_email", None)
                r.pop("supervisor_phone", None)

            # 🎯 Target-based filtering (ROBUST)
            if target:
                full_name = (r.get("first_name", "") + " " + r.get("last_name", "")).lower()
                if target not in full_name:
                    continue

            processed_records.append(r)

        # Replace raw_data with filtered data
        raw_data = processed_records

        # 📞 Contact Query Field Reduction
        if is_contact_query:
            allowed_fields = {"first_name", "last_name", "email", "phone_number"}

            for r in raw_data:
                for k in list(r.keys()):
                    if k not in allowed_fields:
                        r.pop(k, None)

    # Recalculate keys after filtering
    if not is_direct_msg:
        sample = raw_data[0] if isinstance(raw_data, list) and raw_data else raw_data
        if isinstance(sample, dict):
            data_keys = list(sample.keys())

    # ============================================================
    # 4. Prepare LLM Prompt
    # ============================================================
    history_summary = summarize_text(get_chat_context(state["messages"]))

    prompt_text = f"""
            You are the Umbrella Corp HR System. Use simple, clear language.

            HISTORY SUMMARY:
            {history_summary}

            USER ROLE:
            {role}
            """

    if source == "sql" and not is_direct_msg:
        is_multi = isinstance(raw_data, list)
        record_count = len(raw_data) if is_multi else 1

        prompt_text += f"""
            SECURITY CLEARANCE: GRANTED

            RECORDS_FOUND: {record_count}
            AVAILABLE DATA FIELDS: {data_keys}

            --- CORE INSTRUCTION ---
            Generate a response using ONLY placeholders from AVAILABLE DATA FIELDS.

            --- RESPONSE RULES ---

            CASE 1: SINGLE RECORD
            - Use relevant placeholders naturally.

            CASE 2: MULTIPLE RECORDS
            - Use ONLY: {{DATA_TABLE}}
            - Format:
            "I found {record_count} matching records:\\n\\n{{DATA_TABLE}}"

            --- FIELD RULES ---
            1. ONLY use AVAILABLE DATA FIELDS
            2. NEVER invent fields
            3. Skip NULL values

            --- SECURITY ---
            - NEVER output real values
            - ONLY placeholders

            --- STYLE ---
            - Keep it short and professional
            """
    else:
        prompt_text += f"""
        POLICY CONTEXT:
        {raw_data}
        """

    print(f"[DEBUG] Sending prompt to LLM...")

    template_response = llm.invoke([
        SystemMessage(content=prompt_text),
        state["messages"][-1]
    ]).content

    print(f"[DEBUG] LLM Template Response: {template_response}")

    # ============================================================
    # 5. Reverse Masking
    # ============================================================
    final_answer = template_response

    if source == "sql" and not is_direct_msg:
        print("[DEBUG] Performing Reverse Masking...")

        records = raw_data if isinstance(raw_data, list) else [raw_data]

        # ---------- SINGLE ----------
        if len(records) == 1:
            record = records[0]

            if isinstance(record, dict):
                for k, v in record.items():
                    pattern = re.compile(r'\{+\s*' + re.escape(k) + r'\s*\}+')
                    safe_val = "" if v is None else str(v)
                    final_answer = pattern.sub(safe_val, final_answer)

        # ---------- MULTI ----------
        elif len(records) > 1:
            if is_contact_query:
                table_rows = [
                    f"{r.get('first_name')} {r.get('last_name')} | Email: {r.get('email')} | Phone: {r.get('phone_number')}"
                    for r in records
                ]
            else:
                table_rows = [
                    " | ".join(f"{k}: {'' if v is None else v}" for k, v in r.items())
                    for r in records if isinstance(r, dict)
                ]

            combined_table = "\n".join(table_rows)

            table_pattern = re.compile(r'\{+\s*DATA_TABLE\s*\}+')
            final_answer = table_pattern.sub(combined_table, final_answer)

    print(f"[DEBUG] Final Answer: {final_answer}")

    return {"answer": final_answer}

# ============================================================
# AUDIT NODE
# ============================================================
def audit_node(state: AgentState, config: RunnableConfig):
    print("--- NODE: AUDIT ---")

    # Saves the UNMASKED final answer for internal logs
    save_to_audit_log(
        user_id=config["configurable"].get("thread_id", "unknown"),
        question=state["messages"][-1].content if state["messages"] else "N/A",
        answer=state.get("answer", ""),
        source=state.get("source_used", "unknown"),
        node_path=f"router -> {state.get('source_used')} -> generate"
    )

    return state






# #backend/app/agent/nodes.py
# import os
# import re
# import sqlite3
# from dotenv import load_dotenv
# from datetime import datetime
# from typing import Literal
# from pydantic import BaseModel, Field
# from langchain_openai import ChatOpenAI
# from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
# from langchain_core.runnables import RunnableConfig
# from langchain.chains.summarize import load_summarize_chain
# from langchain_core.documents import Document

# from backend.app.agent.state import AgentState
# from backend.app.agent.tools.retriever import get_retriever
# from backend.app.agent.tools.sql_tool import query_employee_db
# from backend.app.db.connection import save_to_audit_log

# load_dotenv()

# llm = ChatOpenAI(
#     model="gpt-4o-mini",
#     temperature=0,
#     api_key=os.getenv("OPENAI_API_KEY")
# )

# # --- HELPER: CONTEXT BUILDER ---
# def get_chat_context(messages, limit=5):
#     """Formats recent messages into a string for the LLM to understand context."""
#     context = ""
#     for msg in messages[-limit:]:
#         role = "User" if isinstance(msg, HumanMessage) else "Assistant"
#         context += f"{role}: {msg.content}\n"
#     return context

# # --- ROUTER LOGIC ---
# # class RouteQuery(BaseModel):
# #     """Route a user query to the most appropriate data source."""
# #     datasource: Literal["sql", "vector"] = Field(
# #         description="Choose 'sql' for personal data/people. Choose 'vector' for general policies."
# #     )

# class RouteQuery(BaseModel):
#     datasource: Literal["sql", "vector"]
#     target_entity: str = Field(
#         description="The name of the person, a Department (e.g., 'IT', 'HR'), or 'SELF'. Use 'NONE' for general policies."
#     )
#     reasoning: str = Field(description="Brief explanation of why this path was chosen.")

# # def router_node(state: AgentState, config: RunnableConfig):
# #     print("--- NODE: ROUTER ---")
# #     user_role = config["configurable"].get("role", "employee")

# #     # FIX: Provide context so the router knows 'him' refers to a person previously discussed
# #     chat_context = get_chat_context(state["messages"])

# #     structured_llm = llm.with_structured_output(RouteQuery)

# #     route = structured_llm.invoke(
# #         f"""
# #         User role: {user_role}
# #         Recent Conversation:
# #         {chat_context}

# #         Rules:
# #         1. Use 'sql' if the question is about a person, contact info, PTO, salary, or relationships.
# #         2. Use 'vector' for company handbooks, dress code, or general 'how-to' policies.
# #         3. If the user uses pronouns (him/her/them) regarding a person mentioned in context, use 'sql'.
# #         """
# #     )

# #     return {"source_used": str(route.datasource).lower()}
# #===================== Routing to proper node =============

# # def router_node(state: AgentState, config: RunnableConfig):
# #     """
# #     Without PII masking and no summery
# #     """
# #     chat_context = get_chat_context(state["messages"])
# #     structured_llm = llm.with_structured_output(RouteQuery)

# #     instructions = f"""
# #     Analyze the history and question to determine the target and datasource.

# #     RULES:
# #     1. Use 'sql' if the query is about a person, department list (e.g. 'IT'), PTO, salary, or contact info.
# #        - Set target_entity to the person's name, department name, or 'SELF'.

# #     2. Use 'vector' if the query is about company policies, rules, handbooks, or general 'how-to' questions.
# #        - Examples: 'What is the dress code?', 'How do I apply for leave?', 'Remote work policy'.
# #        - Set target_entity='NONE'.

# #     History: {chat_context}
# #     Question: {state['messages'][-1].content}
# #     """

# #     result = structured_llm.invoke(instructions)

# #     return {
# #         "source_used": result.datasource.lower(),
# #         "extracted_target": result.target_entity,
# #         "steps": state.get("steps", []) + ["router"] # Keep track of the path
# #     }


# def router_node(state: AgentState, config: RunnableConfig):
#     print("--- NODE: ROUTER (Summarized) ---")

#     # 1. SUMMARIZATION: Use prebuilt chain to condense last 10 messages
#     # This creates a "lemon-simple" summary for the router
#     chat_history_text = "\n".join([f"{m.type}: {m.content}" for m in state["messages"][-10:]])
#     history_doc = [Document(page_content=chat_history_text)]

#     # We use 'stuff' for a quick, direct summary
#     summarize_chain = load_summarize_chain(llm, chain_type="stuff")
#     summary = summarize_chain.invoke(history_doc)

#     # 2. CLASSIFICATION: Use the summary instead of raw history
#     structured_llm = llm.with_structured_output(RouteQuery)

#     instructions = f"""
#     Analyze the conversation summary and the current question to route correctly.

#     RULES:
#     1. Use 'sql' for people, departments, PTO, salary, or contact info.
#        - Target: Person name, Dept (e.g. 'IT'), or 'SELF'.
#     2. Use 'vector' for general company policies, dress code, or handbooks.
#        - Target: 'NONE'.

#     SUMMARY: {summary}
#     QUESTION: {state['messages'][-1].content}
#     """

#     result = structured_llm.invoke(instructions)

#     return {
#         "source_used": result.datasource.lower(),
#         "extracted_target": result.target_entity,
#         "steps": state.get("steps", []) + ["router"]
#     }

# # --- DATA NODES ---
# def retrieve_node(state: AgentState):
#     print("--- NODE: VECTOR SEARCH ---")
#     user_question = state["messages"][-1].content
#     retriever = get_retriever()
#     docs = retriever.invoke(user_question)
#     return {"context": [doc.page_content for doc in docs]}

# # def sql_node(state: AgentState, config: RunnableConfig):
# #     """
# #         Args:
# #         state (AgentState): The current conversation state containing message history.
# #         config (RunnableConfig): Runtime configuration including user identity and role.

# #     Returns:
# #         dict: A dictionary updating the agent state with retrieved SQL context.
# #     """

# #     print("--- NODE: SQL SEARCH ---")

# #     user_id = config["configurable"].get("thread_id", "unknown_user")
# #     user_role = config["configurable"].get("role", "employee")

# #     # FIX: Send the history context to the SQL tool so it can resolve the 'Target' name
# #     chat_context = get_chat_context(state["messages"])

# #     result = query_employee_db(user_id, user_role, chat_context)
# #     print(f"DEBUG SQL RESULT: {result}")
# #     return {"context": [result]}

# def sql_node(state: AgentState, config: RunnableConfig):
#     user_id = config["configurable"].get("thread_id")
#     role = config["configurable"].get("role")

#     # Use the target already found by the smart router
#     target = state.get("extracted_target", "SELF")

#     # Direct DB call, no extra LLM latency!
#     result = query_employee_db(user_id, role, target)
#     return {"context": [result]}

# # --- GENERATION NODE ---
# #====================== Without Masking Data ==================
# # def generate_node(state: AgentState, config: RunnableConfig):
# #     print("--- NODE: GENERATE ---")

# #     latest_context = state.get('context', 'No data found.')

# #     # Check if the context is a list (multiple employees found)
# #     context_str = str(latest_context)

# #     prompt_text = f"""
# #     You are the Umbrella Corp HR System.

# #     DATA RETRIEVED:
# #     {latest_context}

# #     USER ROLE: {config["configurable"].get("role")}

# #     INSTRUCTIONS:
# #     1. If the DATA RETRIEVED contains the person's info, answer the question directly.
# #     2. If the user asks for 'Salary' and the field is missing from the data, explain: "Access Denied: Your security clearance level ({config["configurable"].get("role")}) does not permit viewing salary information for other personnel."
# #     3. Do not say "I couldn't find it" if the person is in the database but the specific field is missing—be honest about the restriction.
# #     """

# #     messages = [
# #         SystemMessage(content=prompt_text),
# #         *state["messages"][-5:]
# #     ]

# #     response = llm.invoke(messages)
# #     return {"answer": response.content}

# def generate_node(state: AgentState, config: RunnableConfig):
#     print("--- NODE: GENERATE (Secure Template Mode) ---")

#     # 1. Prepare the Raw Data
#     # 'context' could be a single dict or a list of dicts from sql_node
#     raw_data = state.get('context', [])

#     # 2. SUMMARIZATION: Condense last 10 messages for context
#     history_text = "\n".join([f"{m.type}: {m.content}" for m in state["messages"][-10:]])
#     summarize_chain = load_summarize_chain(llm, chain_type="stuff")
#     #history_summary = summarize_chain.run([Document(page_content=history_text)])
#     history_summary = summarize_chain.invoke([Document(page_content=history_text)])

#     # 3. MASKING: Identify keys, but hide values from the LLM
#     # We tell the LLM what data exists (keys) without showing the actual PII (values)
#     data_keys = []
#     if isinstance(raw_data, list) and len(raw_data) > 0:
#         data_keys = list(raw_data[0].keys()) if isinstance(raw_data[0], dict) else []
#     elif isinstance(raw_data, dict):
#         data_keys = list(raw_data.keys())

#     prompt_text = f"""
#     You are the Umbrella Corp HR System.

#     CONTEXT SUMMARY: {history_summary}
#     AVAILABLE DATA FIELDS: {data_keys}
#     RECORD COUNT: {len(raw_data) if isinstance(raw_data, list) else 1}

#     INSTRUCTIONS:
#     1. Write a response in simple words.
#     2. Use double curly braces for any data values, e.g., {{first_name}} or {{email}}.
#     3. If 'salary' is requested but not in the AVAILABLE DATA FIELDS, state: "Access Denied: Your security clearance ({config["configurable"].get("role")}) does not permit viewing this."
#     4. For multiple records (e.g., department list), simply say "Here are the results:" and use the placeholder {{DATA_TABLE}}.
#     """

#     # 4. GENERATE: LLM creates the template
#     messages = [
#         SystemMessage(content=prompt_text),
#         state["messages"][-1] # The current user question
#     ]
#     template_response = llm.invoke(messages).content

#     # 5. REVERSE MASKING: Local Swap of Real Data
#     final_answer = template_response

#     if len(raw_data) == 1 or isinstance(raw_data, dict):
#         # Single record swap
#         target_dict = raw_data[0] if isinstance(raw_data, list) else raw_data
#         for key, value in target_dict.items():
#             final_answer = final_answer.replace("{{" + str(key) + "}}", str(value))
#     else:
#         # Multi-record (Department) swap: Build a simple text table locally
#         table_rows = []
#         for emp in raw_data:
#             row = ", ".join([f"{k}: {v}" for k, v in emp.items()])
#             table_rows.append(row)
#         final_answer = final_answer.replace("{{DATA_TABLE}}", "\n".join(table_rows))

#     return {"answer": final_answer}

# # --- AUDIT NODE ---
# def audit_node(state: AgentState, config: RunnableConfig):
#     print("--- NODE: AUDIT LOGGING ---")

#     user_id = config["configurable"].get("thread_id", "unknown_user")
#     source = state.get("source_used", "vector")

#     # The actual question is the last message in the state
#     user_question = state["messages"][-1].content if state["messages"] else "Unknown"
#     current_path = f"router -> {source}_search -> generate"

#     save_to_audit_log(
#         user_id=user_id,
#         question=user_question,
#         answer=state["answer"],
#         source=source,
#         node_path=current_path
#     )

#     return state