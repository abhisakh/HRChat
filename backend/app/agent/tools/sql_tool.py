import sqlite3
from pathlib import Path

# Absolute path to the database
DB_PATH = Path(__file__).parent.parent.parent / "db" / "hr_database.db"

def query_employee_db(user_id: str, user_question: str):
    """
    Fetches employee records from the SQL database for a specific user.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Allows accessing columns by name: row['salary']
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print(f"--- SQL TOOL: Fetching record for {user_id} ---")

        # Security: Always filter by the logged-in user_id
        query = "SELECT * FROM employees WHERE user_id = ?"
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            # Convert the SQLite Row to a dictionary for the LLM to read easily
            data = dict(row)

            # Create a descriptive string of the employee's data
            info_str = (
                f"Employee Record for {data['first_name']} {data['last_name']}:\n"
                f"- Position: {data['position']}\n"
                f"- Department: {data['department']}\n"
                f"- Salary: ${data['salary']:,.2f}\n"
                f"- Available PTO: {data['available_pto']} days\n"
                f"- Hire Date: {data['hire_date']}\n"
                f"- Supervisor: {data['supervisor']}\n"
                f"- Location: {data['location']}\n"
                f"- Skills: {data['skills']}"
            )
            return info_str

        return f"Error: No employee record found for User ID '{user_id}'."

    except Exception as e:
        return f"Error querying database: {str(e)}"