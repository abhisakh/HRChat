# import sqlite3
# from pathlib import Path

# DB_PATH = Path(__file__).parent.parent.parent / "db" / "hr_database.db"

# def query_employee_db(user_id: str, role: str, user_question: str):
#     conn = None
#     try:
#         conn = sqlite3.connect(DB_PATH, timeout=30)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()

#         q_lower = user_question.lower()
#         print(f"--- SQL TOOL: Role={role} | User={user_id} ---")

#         # 1. THE NOISE FILTER (Stop Words)
#         stop_words = {
#             "i", "want", "to", "know", "about", "is", "who", "find",
#             "search", "contact", "details", "for", "tell", "me", "the"
#         }

#         # Split into words and remove the "noise"
#         words = q_lower.split()
#         filtered_words = [w for w in words if w not in stop_words]

#         # The remaining words are our "Target" (e.g., "Dana Adams" or "user_7202")
#         target_name = " ".join(filtered_words).strip().title()

#         # 2. DECIDE: SELF OR SEARCH?
#         # If the question contains 'my' or the target is empty, it's a self-lookup
#         is_self_query = "my" in words or not target_name

#         if is_self_query:
#             cursor.execute("SELECT * FROM employees WHERE user_id = ?", (user_id,))
#         else:
#             # FUZZY SEARCH: Matches First Name, Last Name, or Full Name
#             query = """
#                 SELECT * FROM employees
#                 WHERE (LOWER(first_name) LIKE LOWER(?)
#                    OR LOWER(last_name) LIKE LOWER(?)
#                    OR LOWER(first_name || ' ' || last_name) LIKE LOWER(?)
#                    OR user_id = ?)
#             """
#             # We use the cleaned target_name here
#             search_param = f"%{target_name}%"
#             cursor.execute(query, (search_param, search_param, search_param, target_name))

#         row = cursor.fetchone()

#         if not row:
#             return f"No record found for '{target_name if target_name else user_id}'."

#         # 3. PRIVACY FILTER
#         data = dict(row)
#         is_colleague = data.get('user_id') != user_id

#         if role == "employee":
#             # Hide sensitive fields from standard employees
#             restricted = ['salary', 'ssn', 'performance_notes', 'bank_account']
#             if is_colleague:
#                 restricted.extend(['available_pto', 'hire_date', 'available_sick_leave'])

#             for field in restricted:
#                 data.pop(field, None)

#         return f"{'Directory' if is_colleague else 'Personal'} Result: {data}"

#     except Exception as e:
#         return f"Database error: {str(e)}"
#     finally:
#         if conn: conn.close()

import os
import sqlite3
import re
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Load Environment Variables
load_dotenv()

DB_PATH = Path(__file__).parent.parent.parent / "db" / "hr_database.db"

# 2. Initialize a local, fast LLM for extraction
# We keep temperature at 0 for strict entity extraction
extractor_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

def extract_target_with_llm(user_question: str):
    """Refined extraction logic to prevent 'i' or 'need' from breaking SQL."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an entity extractor for an HR database. "
            "Identify the subject of the user's query. "
            "- If searching for themselves: return 'SELF'. "
            "- If searching for a person: return ONLY the full name (e.g., 'John Doe'). "
            "- If searching by ID: return ONLY the ID (e.g., 'user_123'). "
            "Ignore all filler like 'find', 'who is', 'give me data for'."
        )),
        ("user", "{question}")
    ])

    chain = prompt | extractor_llm | StrOutputParser()
    return chain.invoke({"question": user_question}).strip().replace('"', '')

def query_employee_db(user_id: str, role: str, user_question: str):
    """
    Unified Tool: Extracts the name using LLM, then queries SQLite.
    """
    conn = None
    try:
        # Step A: The 'Mini-Brain' extraction
        target = extract_target_with_llm(user_question)
        print(f"--- [DEBUG] LLM Extracted: '{target}' from '{user_question}' ---")

        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Step B: Logic Switch (Self vs. Others)
        if target.upper() in ["SELF", "ME", "MY"] or target == user_id:
            cursor.execute("SELECT * FROM employees WHERE user_id = ?", (user_id,))
        else:
            search_param = f"%{target}%"
            query = """
                SELECT * FROM employees
                WHERE (first_name || ' ' || last_name) LIKE ?
                   OR first_name LIKE ?
                   OR last_name LIKE ?
                   OR user_id = ?
            """
            cursor.execute(query, (search_param, search_param, search_param, target))

        row = cursor.fetchone()
        if not row:
            return f"Access Denied or Record Not Found: '{target}'."

        # Step C: RBAC Security Layer
        data = dict(row)
        if role == "employee" and data['user_id'] != user_id:
            # Shield sensitive fields from peers
            public_fields = ['first_name', 'last_name', 'position', 'department', 'email']
            data = {k: v for k, v in data.items() if k in public_fields}

        return data

    except Exception as e:
        return f"Database Error: {str(e)}"
    finally:
        if conn: conn.close()