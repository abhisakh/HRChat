# import sqlite3
# import random
# from faker import Faker
# from datetime import datetime, timedelta
# from pathlib import Path

# # Paths
# DB_PATH = Path(__file__).parent.parent.parent / "backend" / "app" / "db" / "hr_database.db"
# fake = Faker()

# def generate_and_seed_employees(num_employees=50):
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     print(f"🌱 Seeding {num_employees} employees into {DB_PATH}...")

#     for _ in range(num_employees):
#         employee_id = f"user_{random.randint(100, 999)}" # Simple IDs for easier testing
#         first_name = fake.first_name()
#         last_name = fake.last_name()
#         skills = ", ".join(random.sample(["Python", "Data Analysis", "Security", "Leadership"], k=2))

#         cursor.execute("""
#             INSERT OR IGNORE INTO employees
#             (user_id, first_name, last_name, email, phone_number, position, department, skills, location, hire_date, supervisor, salary)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """, (
#             employee_id, first_name, last_name, fake.email(), fake.phone_number(),
#             random.choice(["Software Engineer", "HR Specialist", "Security Officer"]),
#             random.choice(["IT", "HR", "Security"]),
#             skills, random.choice(["Raccoon City HQ", "Umbrella Europe"]),
#             (datetime.now() - timedelta(days=random.randint(1, 3000))).strftime("%Y-%m-%d"),
#             fake.name(), round(random.uniform(40000, 120000), 2)
#         ))

#     conn.commit()
#     conn.close()
#     print("✅ Seeding complete.")

# if __name__ == "__main__":
#     generate_and_seed_employees(20)

#------------------------------------------------------------
#____________________ PASSWORD INCORPORATION ________________
#------------------------------------------------------------
# import sqlite3
# import random
# import hashlib
# import sys
# from faker import Faker
# from datetime import datetime, timedelta
# from pathlib import Path
# #from backend.app.db.connection import init_db, DB_PATH

# # --- NEW: Fix pathing to import backend modules ---
# # This looks 3 levels up from data/scripts to the project root
# ROOT_DIR = Path(__file__).parent.parent.parent
# sys.path.append(str(ROOT_DIR))

# from backend.app.db.connection import init_db

# DB_PATH = ROOT_DIR / "backend" / "app" / "db" / "hr_database.db"
# fake = Faker()

# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# def generate_and_seed_employees(num_employees=20):
#     # 1. Rebuild the entire database structure first
#     print("🏗️  Building database schemas from SQL files...")
#     init_db()

#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     print(f"🌱 Seeding {num_employees} employees and credentials...")

#     for _ in range(num_employees):
#         employee_id = f"user_{random.randint(100, 999)}"
#         first_name = fake.first_name()
#         last_name = fake.last_name()

#         # Seed Employee Data
#         cursor.execute("""
#             INSERT OR IGNORE INTO employees
#             (user_id, first_name, last_name, email, phone_number, position, department, skills, location, hire_date, supervisor, salary)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """, (
#             employee_id, first_name, last_name, fake.email(), fake.phone_number(),
#             random.choice(["Software Engineer", "HR Specialist", "Security Officer"]),
#             random.choice(["IT", "HR", "Security"]),
#             ", ".join(random.sample(["Python", "Security", "AI"], k=2)),
#             random.choice(["Raccoon City HQ", "Umbrella Europe"]),
#             (datetime.now() - timedelta(days=random.randint(1, 3000))).strftime("%Y-%m-%d"),
#             fake.name(), round(random.uniform(40000, 120000), 2)
#         ))

#         # Seed Auth Data
#         username = first_name.lower()
#         cursor.execute("""
#             INSERT OR IGNORE INTO users (user_id, username, password_hash)
#             VALUES (?, ?, ?)
#         """, (employee_id, username, hash_password("password123")))

#     conn.commit()
#     conn.close()
#     print("✅ Seeding complete. Every user's password is 'password123'.")

# if __name__ == "__main__":
#     generate_and_seed_employees(20)


#------------------------------------------------------------
#____________________ RBAC INCORPORATION ________________
#------------------------------------------------------------

# import sqlite3
# import random
# import hashlib
# import sys
# from faker import Faker
# from datetime import datetime, timedelta
# from pathlib import Path

# # --- Setup paths to import backend modules ---
# ROOT_DIR = Path(__file__).parent.parent.parent
# sys.path.append(str(ROOT_DIR))

# from backend.app.db.connection import init_db  # Database initialization

# # --- Constants ---
# DB_PATH = ROOT_DIR / "backend" / "app" / "db" / "hr_database.db"
# fake = Faker()

# # --- Helper Functions ---
# def hash_password(password: str) -> str:
#     """Return SHA256 hash of the password."""
#     return hashlib.sha256(password.encode()).hexdigest()

# # --- Main Seeding Function ---
# def generate_and_seed_employees(num_employees: int = 20):
#     print("🏗️  Building database schemas from SQL files...")
#     init_db()  # Ensure tables exist

#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     print(f"🌱 Seeding {num_employees} employees with credentials and roles...")

#     for _ in range(num_employees):
#         employee_id = f"user_{random.randint(100, 999)}"
#         first_name = fake.first_name()
#         last_name = fake.last_name()

#         # Seed Employee Data
#         cursor.execute("""
#             INSERT OR IGNORE INTO employees
#             (user_id, first_name, last_name, email, phone_number, position, department, skills, location, hire_date, supervisor, salary)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """, (
#             employee_id,
#             first_name,
#             last_name,
#             fake.email(),
#             fake.phone_number(),
#             random.choice(["Software Engineer", "HR Specialist", "Security Officer"]),
#             random.choice(["IT", "HR", "Security"]),
#             ", ".join(random.sample(["Python", "Security", "AI"], k=2)),
#             random.choice(["Raccoon City HQ", "Umbrella Europe"]),
#             (datetime.now() - timedelta(days=random.randint(1, 3000))).strftime("%Y-%m-%d"),
#             fake.name(),
#             round(random.uniform(40000, 120000), 2)
#         ))

#         # Seed Auth Data with role
#         username = first_name.lower()
#         role = random.choice(["employee", "hr", "admin"])
#         cursor.execute("""
#             INSERT OR IGNORE INTO users (user_id, username, password_hash, role)
#             VALUES (?, ?, ?, ?)
#         """, (employee_id, username, hash_password("password123"), role))

#         print(f"Seeded user: {username} (ID: {employee_id}) with role: {role}")

#     conn.commit()
#     conn.close()
#     print("✅ Seeding complete. Default password is 'password123' for all users.")

# # --- Run Script ---
# if __name__ == "__main__":
#     generate_and_seed_employees(20)

#------------------------------------------------------------
#____________________ AUTO + MANUAL EMPLOYEE ADDITION INCORPORATION ________________
#------------------------------------------------------------
import sqlite3
import random
import hashlib
import sys
from faker import Faker
from datetime import datetime, timedelta
from pathlib import Path

# --- Setup paths to import backend modules ---
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR))

from backend.app.db.connection import init_db  # Database initialization

# --- Constants ---
DB_PATH = ROOT_DIR / "backend" / "app" / "db" / "hr_database.db"
fake = Faker()
VALID_ROLES = ["employee", "hr", "admin"]

# --- Helper Functions ---
def hash_password(password: str) -> str:
    """Standardized SHA256 hashing with string cleaning."""
    clean_p = str(password).strip()
    return hashlib.sha256(clean_p.encode('utf-8')).hexdigest()

def input_with_validation(prompt: str, valid_options: list = None, default: str = None):
    """Helper to get input with optional validation."""
    while True:
        value = input(prompt).strip()
        if not value and default is not None:
            return default
        if valid_options:
            if value.lower() in valid_options:
                return value.lower()
            print(f"Invalid input. Choose one of: {', '.join(valid_options)}")
        else:
            if value:
                return value

# --- Main Seeding Function ---
# --- Main Seeding Function ---
def generate_and_seed_employees(num_employees: int = 20, manual: bool = False):
    print("🏗️  Building database schemas from SQL files...")
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"🌱 Seeding {num_employees} employees with credentials and roles...")

    existing_ids = []  # ✅ track created employees

    for _ in range(num_employees):
        employee_id = f"user_{random.randint(1000, 9999)}"

        # --- Assign supervisor FIRST (from existing employees) ---
        supervisor_id = random.choice(existing_ids) if existing_ids else None

        if manual:
            print("\n--- Enter employee details ---")
            first_name = input_with_validation("First Name: ")
            last_name = input_with_validation("Last Name: ")
            username = input_with_validation("Username: ")
            password = input_with_validation("Password (default: password123): ", default="password123")
            position = input_with_validation("Position: ")
            salary = float(input_with_validation("Salary: "))
            role = input_with_validation(f"Role ({'/'.join(VALID_ROLES)}): ", VALID_ROLES)
            email = input_with_validation("Email (optional): ", default=fake.email())
            phone_number = input_with_validation("Phone number (optional): ", default=fake.phone_number())
            department = input_with_validation("Department (optional): ", default=random.choice(["IT", "HR", "Security"]))

            # ✅ Skills as list (not string)
            raw_skills = input_with_validation(
                "Skills (comma separated, optional): ",
                default="Python, AI"
            )
            skills_list = [s.strip().upper() for s in raw_skills.split(",") if s.strip()]

            location = input_with_validation("Location (optional): ", default=random.choice(["Raccoon City HQ", "Umbrella Europe"]))
            hire_date = input_with_validation(
                "Hire Date (YYYY-MM-DD, optional): ",
                default=(datetime.now() - timedelta(days=random.randint(1, 3000))).strftime("%Y-%m-%d")
            )

        else:
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = first_name.lower()
            password = "password123"
            position = random.choice(["Software Engineer", "HR Specialist", "Security Officer"])
            salary = round(random.uniform(40000, 120000), 2)
            role = random.choice(VALID_ROLES)
            email = fake.email()
            phone_number = fake.phone_number()
            department = random.choice(["IT", "HR", "Security"])

            # ✅ Skills list (normalized)
            skills_list = random.sample(["PYTHON", "SECURITY", "AI"], k=2)

            location = random.choice(["Raccoon City HQ", "Umbrella Europe"])
            hire_date = (datetime.now() - timedelta(days=random.randint(1, 3000))).strftime("%Y-%m-%d")

        # --- Hash password ---
        p_hash = hash_password(password)
        print(f"DEBUG: Hashing string: '{password}' | Hash: {p_hash}")

        # --- Insert employee (NO skills, NO supervisor name anymore) ---
        cursor.execute("""
            INSERT OR IGNORE INTO employees
            (user_id, first_name, last_name, email, phone_number,
             position, department, location, hire_date,
             supervisor_id, salary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            employee_id,
            first_name,
            last_name,
            email,
            phone_number,
            position,
            department,
            location,
            hire_date,
            supervisor_id,
            salary
        ))

        # --- Insert skills into separate table ---
        for skill in skills_list:
            cursor.execute("""
                INSERT INTO employee_skills (user_id, skill)
                VALUES (?, ?)
            """, (employee_id, skill))

        # --- Insert auth data ---
        cursor.execute("""
            INSERT OR IGNORE INTO users (user_id, username, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (employee_id, username, p_hash, role))

        print(f"Seeded user: {username} (ID: {employee_id}) with role: {role}")

        # ✅ Add AFTER insert
        existing_ids.append(employee_id)

    conn.commit()
    conn.close()
    print("✅ Seeding complete. Use 'password123' (or your manual entry) to log in.")

# --- Run Script ---
if __name__ == "__main__":
    mode = input_with_validation("Seed manually? (yes/no, default: no): ", valid_options=["yes", "no"], default="no")
    manual_mode = True if mode == "yes" else False
    num = int(input_with_validation("Number of employees to seed (default: 5): ", default="5"))
    generate_and_seed_employees(num_employees=num, manual=manual_mode)