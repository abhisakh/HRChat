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

# --- Helper Functions ---
def hash_password(password: str) -> str:
    """Return SHA256 hash of the password."""
    return hashlib.sha256(password.encode()).hexdigest()

# --- Main Seeding Function ---
def generate_and_seed_employees(num_employees: int = 20):
    print("🏗️  Building database schemas from SQL files...")
    init_db()  # Ensure tables exist

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"🌱 Seeding {num_employees} employees with credentials and roles...")

    for _ in range(num_employees):
        employee_id = f"user_{random.randint(100, 999)}"
        first_name = fake.first_name()
        last_name = fake.last_name()

        # Seed Employee Data
        cursor.execute("""
            INSERT OR IGNORE INTO employees
            (user_id, first_name, last_name, email, phone_number, position, department, skills, location, hire_date, supervisor, salary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            employee_id,
            first_name,
            last_name,
            fake.email(),
            fake.phone_number(),
            random.choice(["Software Engineer", "HR Specialist", "Security Officer"]),
            random.choice(["IT", "HR", "Security"]),
            ", ".join(random.sample(["Python", "Security", "AI"], k=2)),
            random.choice(["Raccoon City HQ", "Umbrella Europe"]),
            (datetime.now() - timedelta(days=random.randint(1, 3000))).strftime("%Y-%m-%d"),
            fake.name(),
            round(random.uniform(40000, 120000), 2)
        ))

        # Seed Auth Data with role
        username = first_name.lower()
        role = random.choice(["employee", "hr", "admin"])
        cursor.execute("""
            INSERT OR IGNORE INTO users (user_id, username, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (employee_id, username, hash_password("password123"), role))

        print(f"Seeded user: {username} (ID: {employee_id}) with role: {role}")

    conn.commit()
    conn.close()
    print("✅ Seeding complete. Default password is 'password123' for all users.")

# --- Run Script ---
if __name__ == "__main__":
    generate_and_seed_employees(20)