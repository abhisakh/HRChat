CREATE TABLE IF NOT EXISTS employees (
    user_id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone_number TEXT,
    position TEXT,
    department TEXT,
    location TEXT,
    hire_date DATE,
    supervisor_id TEXT,
    salary REAL,
    available_pto INTEGER DEFAULT 15,

    FOREIGN KEY (supervisor_id) REFERENCES employees(user_id)
);

CREATE TABLE IF NOT EXISTS employee_skills (
    user_id TEXT,
    skill TEXT,
    FOREIGN KEY (user_id) REFERENCES employees(user_id)
);