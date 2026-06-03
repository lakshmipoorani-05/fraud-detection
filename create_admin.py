import sqlite3
from werkzeug.security import generate_password_hash
import os

def create_admin(username, email, password):
    db_path = 'fraud.db'
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables if they don't exist (just in case)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'pending',
            organization TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Check if user already exists
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        print(f"User {username} already exists. Updating to admin...")
        cursor.execute(
            "UPDATE users SET role='admin', status='approved' WHERE username=?",
            (username,)
        )
    else:
        # Create user
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, email, password, role, status, organization) VALUES (?,?,?,?,?,?)",
            (username, email, hashed_password, 'admin', 'approved', 'Internal')
        )
        print(f"Admin user '{username}' created successfully!")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Default admin credentials
    ADMIN_USER = "admin"
    ADMIN_EMAIL = "admin@fraud-detection.info"
    ADMIN_PASS = "admin123"
    
    print("--- Fraud Detection Admin Bootstrap ---")
    create_admin(ADMIN_USER, ADMIN_EMAIL, ADMIN_PASS)
    print(f"Credentials:\n  Username: {ADMIN_USER}\n  Password: {ADMIN_PASS}")
    print("---------------------------------------")
