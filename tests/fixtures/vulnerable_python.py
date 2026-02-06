import pickle

# Unsafe deserialization (pickle)
def load_user_data(data: bytes):
    user = pickle.loads(data)
    return user

# SQL Injection
def get_user_by_name(name: str):
    query = f"SELECT * FROM users WHERE name = '{name}'"
    return db.execute(query)

# Weak cryptography
from hashlib import md5

def hash_password(password: str):
    return md5(password.encode()).hexdigest()

# Command injection
import subprocess

def process_file(filename: str):
    result = subprocess.run(f"cat {filename}", shell=True)
    return result
