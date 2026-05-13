# #backend/app/agent/tools/sql_tool.py
import re
import json
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / "db" / "hr_database.db"

ALLOWED_ROLES_FULL_ACCESS = {"admin", "hr"}

def query_employee_db(user_id: str, role: str, target: str):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        role = role.lower()
        clean_target = re.sub(r'\b(department|dept|team|office)\b', '', target, flags=re.IGNORECASE).strip()
        target_upper = clean_target.upper()
        current_year = datetime.now().year

        # --- Base query (clean supervisor join) ---
        base_query = """
            SELECT e.*,
                   s.first_name || ' ' || s.last_name AS supervisor_name,
                   s.email AS supervisor_email,
                   s.phone_number AS supervisor_phone
            FROM employees e
            LEFT JOIN employees s ON e.supervisor_id = s.user_id
        """

        # --- 1. SELF lookup ---
        if target_upper in {"SELF", "ME", "MY"}:
            cursor.execute(f"{base_query} WHERE e.user_id = ?", (user_id,))
            row = cursor.fetchone()
            return {"status": "ok", "data": dict(row)} if row else {"status": "error", "message": "User not found"}

        # --- 2. Total Headcount ---
        if target_upper in {"TOTAL_COUNT", "EMPLOYEE_COUNT", "COMPANY"}:
            cursor.execute("SELECT COUNT(*) FROM employees")
            return {"status": "ok", "data": cursor.fetchone()[0]}

        # --- 3. Department Distribution ---
        if target_upper in {"DEPARTMENTS", "DISTRIBUTION"}:
            cursor.execute("""
                SELECT department, COUNT(*) as count
                FROM employees
                GROUP BY department
                ORDER BY count DESC
            """)
            return {"status": "ok", "data": [dict(r) for r in cursor.fetchall()]}

        # --- 4. Managers (Span of Control) ---
        if target_upper == "MANAGERS":
            cursor.execute("""
                SELECT s.first_name || ' ' || s.last_name AS manager,
                       COUNT(e.user_id) as reports
                FROM employees e
                JOIN employees s ON e.supervisor_id = s.user_id
                GROUP BY e.supervisor_id
                ORDER BY reports DESC
            """)
            return {"status": "ok", "data": [dict(r) for r in cursor.fetchall()]}

        # --- 5. Skill Search ---
        if target_upper.startswith("SKILL_"):
            skill = target_upper.replace("SKILL_", "")
            cursor.execute("""
                SELECT e.first_name, e.last_name, e.department, es.skill
                FROM employee_skills es
                JOIN employees e ON es.user_id = e.user_id
                WHERE es.skill = ?
            """, (skill,))
            return {"status": "ok", "data": [dict(r) for r in cursor.fetchall()]}

        # --- 6. Tenure Alerts ---
        if target_upper == "TENURE_ALERTS":
            threshold = f"{current_year - 5}-01-01"
            cursor.execute("""
                SELECT first_name, last_name, hire_date
                FROM employees
                WHERE DATE(hire_date) <= DATE(?)
            """, (threshold,))
            return {"status": "ok", "data": [dict(r) for r in cursor.fetchall()]}

        # --- 7. Burnout Risk ---
        if target_upper == "BURNOUT_RISK":
            cursor.execute("""
                SELECT first_name, last_name, available_pto
                FROM employees
                WHERE available_pto > 12
            """)
            return {"status": "ok", "data": [dict(r) for r in cursor.fetchall()]}

        # --- 8. Salary Stats (RBAC) ---
        if target_upper == "SALARY_STATS":
            if role not in ALLOWED_ROLES_FULL_ACCESS:
                return {"status": "error", "message": "Access Denied"}

            cursor.execute("""
                SELECT department, ROUND(AVG(salary), 2) as avg_salary
                FROM employees
                GROUP BY department
            """)
            return {"status": "ok", "data": [dict(r) for r in cursor.fetchall()]}

        # --- 9. Reports by Manager ---
        if target_upper.startswith("REPORTS_"):
            manager_name = target_upper.replace("REPORTS_", "").strip()
            cursor.execute(f"""
                {base_query}
                WHERE UPPER(s.first_name || ' ' || s.last_name) = ?
                   OR UPPER(s.last_name) = ?
            """, (manager_name, manager_name))
            rows = cursor.fetchall()

        # --- 10. General Search (The Michael Fix) ---
        else:
            pattern = f"%{clean_target}%"
            cursor.execute(f"""
                {base_query}
                WHERE e.user_id = ?
                   OR (UPPER(e.first_name) || ' ' || UPPER(e.last_name)) LIKE ?
                   OR UPPER(e.first_name) = ?
                   OR UPPER(e.department) = ?
            """, (user_id, pattern, target_upper, target_upper))
            rows = cursor.fetchall()

        if not rows:
            return {"status": "error", "message": f"No records found for '{target}'"}

        # --- RBAC filtering ---
        results = []
        for r in rows:
            d = dict(r)

            # 🔒 Security: Strip PII if not self or admin/hr
            if not (d['user_id'] == user_id or role in ALLOWED_ROLES_FULL_ACCESS):
                for f in ['salary', 'available_pto', 'hire_date', 'user_id']:
                    d.pop(f, None)

            results.append(d)

        # Return list if multiple, single dict if one
        return {"status": "ok", "data": results if len(results) > 1 else results[0]}

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        if conn:
            conn.close()

# def query_employee_db(user_id: str, role: str, target: str):
#     conn = None
#     try:
#         conn = sqlite3.connect(DB_PATH, timeout=30)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()

#         target_upper = target.upper()

#         # --- 1. DYNAMIC AGGREGATE: Company-wide Count ---
#         if target_upper in ["NONE", "TOTAL_COUNT", "COMPANY", "EMPLOYEE_COUNT"]:
#             cursor.execute("SELECT COUNT(*) FROM employees")
#             count = cursor.fetchone()[0]
#             return f"There are currently {count} employees at Umbrella Corp."

#         # --- 2. DYNAMIC GROUPING: Department Stats ---
#         # Triggered by queries like "How many departments?" or "List departments"
#         if target_upper in ["DEPARTMENTS", "DEPT_LIST"]:
#             cursor.execute("SELECT department, COUNT(*) as count FROM employees GROUP BY department")
#             rows = cursor.fetchall()
#             return [dict(row) for row in rows]

#         # --- 3. DYNAMIC FILTER: Departmental Membership ---
#         # If the target looks like a department name
#         cursor.execute("SELECT DISTINCT department FROM employees")
#         depts = [d['department'].upper() for d in cursor.fetchall()]

#         if target_upper in depts:
#             cursor.execute("SELECT * FROM employees WHERE UPPER(department) = ?", (target_upper,))

#         # --- 4. INDIVIDUAL SEARCH: Name, ID, or Self ---
#         elif target_upper in ["SELF", "ME", "MY"] or target == user_id:
#             cursor.execute("SELECT * FROM employees WHERE user_id = ?", (user_id,))
#         else:
#             search_param = f"%{target}%"
#             query = """
#                 SELECT * FROM employees
#                 WHERE user_id = ?
#                    OR (first_name || ' ' || last_name) LIKE ?
#                    OR first_name LIKE ?
#                    OR last_name LIKE ?
#             """
#             cursor.execute(query, (target, search_param, search_param, search_param))

#         rows = cursor.fetchall()
#         if not rows:
#             return f"No records found for '{target}'."

#         # --- 5. RBAC ENFORCEMENT & PII MASKING ---
#         results = []
#         for row in rows:
#             data = dict(row)

#             # Check if current user has permission to see this specific record's salary
#             is_own_record = (data['user_id'] == user_id)
#             is_privileged_role = (role.lower() in ["admin", "hr"])

#             if not is_own_record and not is_privileged_role:
#                 # Remove sensitive fields for peer-to-peer or unauthorized lookups
#                 data.pop('salary', None)
#                 data.pop('available_pto', None) # Masking PTO as well for peers

#             results.append(data)

#         # Return a list for multiple results (e.g., department list)
#         # or a single dict for specific employee lookups
#         return results if len(results) > 1 else results[0]

#     except Exception as e:
#         return f"Error: {str(e)}"
#     finally:
#         if conn: conn.close()

# def query_employee_db(user_id: str, role: str, target: str):
#     conn = None
#     try:
#         conn = sqlite3.connect(DB_PATH, timeout=30)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()

#         # Handle "Self"
#         if target.upper() in ["SELF", "ME", "MY"] or target == user_id:
#             cursor.execute("SELECT * FROM employees WHERE user_id = ?", (user_id,))
#         else:
#             # Search by Name, Department, or ID
#             search_param = f"%{target}%"
#             query = """
#                 SELECT * FROM employees
#                 WHERE user_id = ?
#                    OR (first_name || ' ' || last_name) LIKE ?
#                    OR first_name LIKE ?
#                    OR last_name LIKE ?
#                    OR department LIKE ?
#             """
#             cursor.execute(query, (target, search_param, search_param, search_param, search_param))

#         rows = cursor.fetchall()
#         if not rows:
#             return f"No records found for '{target}'."

#         results = []
#         for row in rows:
#             data = dict(row)
#             # RBAC: Only Admin/HR can see salaries of others
#             if role not in ["admin", "hr"] and data['user_id'] != user_id:
#                 # Remove salary and other sensitive fields for peer-to-peer lookups
#                 data.pop('salary', None)
#                 # Keep public info
#             results.append(data)

#         return results if len(results) > 1 else results[0]

#     except Exception as e:
#         return f"Error: {str(e)}"
#     finally:
#         if conn: conn.close()


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