import sqlite3
from pathlib import Path

# Absolute path to the database
DB_PATH = Path(__file__).parent.parent.parent / "db" / "hr_database.db"

def query_employee_db(user_id: str, role: str, user_question: str):
    """
    Role-Based Access Control for employee data.
    """

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print(f"--- SQL TOOL: Role={role} | User={user_id} ---")

        # =========================
        # 👤 EMPLOYEE ACCESS
        # =========================
        if role == "employee":
            query = """
                SELECT first_name, last_name, position, department,
                       available_pto, hire_date, supervisor, location, skills
                FROM employees
                WHERE user_id = ?
            """
            cursor.execute(query, (user_id,))
            row = cursor.fetchone()

            if not row:
                return f"No record found for user {user_id}"

            data = dict(row)

            return (
                f"Your Employee Record:\n"
                f"- Name: {data['first_name']} {data['last_name']}\n"
                f"- Position: {data['position']}\n"
                f"- Department: {data['department']}\n"
                f"- Available PTO: {data['available_pto']} days\n"
                f"- Hire Date: {data['hire_date']}\n"
                f"- Supervisor: {data['supervisor']}\n"
                f"- Location: {data['location']}\n"
                f"- Skills: {data['skills']}\n"
                f"(Salary information is restricted.)"
            )

        # =========================
        # 👨‍💼 HR ACCESS
        # =========================
        elif role == "hr":
            query = "SELECT * FROM employees"
            cursor.execute(query)
            rows = cursor.fetchall()

            return f"HR View: Retrieved {len(rows)} employee records."

        # =========================
        # 🛠 ADMIN ACCESS
        # =========================
        elif role == "admin":
            query = "SELECT * FROM employees"
            cursor.execute(query)
            rows = cursor.fetchall()

            return f"Admin View: Retrieved {len(rows)} employee records."

        # =========================
        # ❌ UNKNOWN ROLE
        # =========================
        else:
            return "Access denied: Invalid role."

    except Exception as e:
        return f"Database error: {str(e)}"

    finally:
        conn.close()