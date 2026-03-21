CREATE TABLE IF NOT EXISTS employees (
    user_id TEXT PRIMARY KEY, -- This will map to employee_id
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone_number TEXT,
    position TEXT,
    department TEXT,
    skills TEXT,           -- Stored as a string
    location TEXT,
    hire_date DATE,
    supervisor TEXT,
    salary REAL,
    available_pto INTEGER DEFAULT 15 -- Added for our PTO logic
);