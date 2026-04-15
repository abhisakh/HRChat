# #backend/app/agent/tools/sql_tool.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "db" / "hr_database.db"

def query_employee_db(user_id: str, role: str, target: str):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Handle "Self"
        if target.upper() in ["SELF", "ME", "MY"] or target == user_id:
            cursor.execute("SELECT * FROM employees WHERE user_id = ?", (user_id,))
        else:
            # Search by Name, Department, or ID
            search_param = f"%{target}%"
            query = """
                SELECT * FROM employees
                WHERE user_id = ?
                   OR (first_name || ' ' || last_name) LIKE ?
                   OR first_name LIKE ?
                   OR last_name LIKE ?
                   OR department LIKE ?
            """
            cursor.execute(query, (target, search_param, search_param, search_param, search_param))

        rows = cursor.fetchall()
        if not rows:
            return f"No records found for '{target}'."

        results = []
        for row in rows:
            data = dict(row)
            # RBAC: Only Admin/HR can see salaries of others
            if role not in ["admin", "hr"] and data['user_id'] != user_id:
                # Remove salary and other sensitive fields for peer-to-peer lookups
                data.pop('salary', None)
                # Keep public info
            results.append(data)

        return results if len(results) > 1 else results[0]

    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if conn: conn.close()


# import os
# import sqlite3
# import re
# from pathlib import Path
# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser

# # 1. Load Environment Variables
# load_dotenv()

# # Path to your SQLite database
# DB_PATH = Path(__file__).parent.parent.parent / "db" / "hr_database.db"

# # 2. Initialize a local, fast LLM for entity extraction
# # We keep temperature at 0 for strict, reliable extraction
# extractor_llm = ChatOpenAI(
#     model="gpt-4o-mini",
#     temperature=0,
#     api_key=os.getenv("OPENAI_API_KEY")
# )

# def extract_target_with_llm(user_question: str, history: str = ""):
#     """
#     Refined extraction logic that uses Conversation History to resolve
#     pronouns like 'him', 'her', 'boss', or 'they'.
#     """
#     prompt = ChatPromptTemplate.from_messages([
#         ("system", (
#             "You are an entity extractor for an Umbrella Corp HR database. "
#             "Your job is to identify the SUBJECT (person or ID) of the query."
#             "\n\nCRITICAL CONTEXT RULES:"
#             "1. If the current question uses pronouns (him, her, he, she, they) or "
#             "   titles like 'my boss' or 'that person', look at the CONVERSATION HISTORY "
#             "   to find the specific name mentioned previously."
#             "2. If the user is asking about themselves ('my', 'me', 'I'): return 'SELF'."
#             "3. If searching for a person: return ONLY their full name (e.g., 'Stacy Harrell')."
#             "4. If searching by ID: return ONLY the ID (e.g., 'user_123')."
#             "5. DO NOT hallucinate names like 'John Doe'. If no name is found in history "
#             "   or the question, return 'NONE'."
#         )),
#         ("user", "CONVERSATION HISTORY:\n{history}\n\nCURRENT QUESTION: {question}")
#     ])

#     chain = prompt | extractor_llm | StrOutputParser()

#     # We strip quotes and extra whitespace to ensure clean SQL parameters
#     result = chain.invoke({"question": user_question, "history": history})
#     return result.strip().replace('"', '').replace("'", "")

# def query_employee_db(user_id: str, role: str, context_string: str):
#     """
#     Unified Tool: Extracts the target from a context-aware string,
#     then performs a secure SQL query.
#     """
#     conn = None
#     try:
#         # Note: 'context_string' now contains both history and the new question
#         # from the graph_node update.
#         target = extract_target_with_llm(context_string)

#         print(f"--- [DEBUG] LLM Extracted Target: '{target}' ---")

#         if target == "NONE":
#             return "I'm sorry, I couldn't identify who you are asking about. Could you please provide a name?"

#         conn = sqlite3.connect(DB_PATH, timeout=30)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()

#         # Step B: Logic Switch (Self vs. Others)
#         if target.upper() in ["SELF", "ME", "MY"] or target == user_id:
#             cursor.execute("SELECT * FROM employees WHERE user_id = ?", (user_id,))
#         else:
#             # Fuzzy matching for names or direct ID match
#             search_param = f"%{target}%"
#             query = """
#                 SELECT * FROM employees
#                 WHERE (first_name || ' ' || last_name) LIKE ?
#                    OR first_name LIKE ?
#                    OR last_name LIKE ?
#                    OR user_id = ?
#             """
#             cursor.execute(query, (search_param, search_param, search_param, target))

#         row = cursor.fetchone()
#         if not row:
#             return f"Access Denied or Record Not Found: '{target}'."

#         # Step C: RBAC Security Layer (Same as before)
#         data = dict(row)

#         # If a regular employee is looking up someone else
#         if role == "employee" and data['user_id'] != user_id:
#             # Shield sensitive fields from peers
#             public_fields = ['first_name', 'last_name', 'position', 'department', 'email', 'phone_number', 'location', 'supervisor']
#             data = {k: v for k, v in data.items() if k in public_fields}

#         return data

#     except Exception as e:
#         return f"Database Error: {str(e)}"
#     finally:
#         if conn: conn.close()