import hashlib

def test_password_hash():
    password = "password123"
    hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()

    assert len(hashed) == 64

def test_hash_consistency():
    password = "password123"
    h1 = hashlib.sha256(password.encode()).hexdigest()
    h2 = hashlib.sha256(password.encode()).hexdigest()

    assert h1 == h2