import psycopg2
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    # Connect directly to the Supabase PostgreSQL server.
    return psycopg2.connect(os.environ.get("SUPABASE_DB_URI"))

def init_db():
    conn = get_conn()
    conn.autocommit = True
    cur = conn.cursor()
    
    # Create table if not exists with PostgreSQL syntax
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            pwd VARCHAR(255) NOT NULL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            type VARCHAR(20) NOT NULL,
            category VARCHAR(50) NOT NULL,
            date DATE NOT NULL,
            description TEXT,
            payment_mode VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    
    # Auto-migration checks for existing databases
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='transactions' AND column_name='payment_mode';")
    if not cur.fetchone():
        cur.execute("ALTER TABLE transactions ADD COLUMN payment_mode VARCHAR(50) DEFAULT 'Cash';")
        
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='transactions' AND column_name='created_at';")
    if not cur.fetchone():
        cur.execute("ALTER TABLE transactions ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")

    cur.close()
    conn.close()

def reg_user(name, email, pwd):
    conn = get_conn()
    cur = conn.cursor()
    try:
        hpwd = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
        cur.execute("INSERT INTO users (name, email, pwd) VALUES (%s,%s,%s) RETURNING id", (name, email, hpwd))
        uid = cur.fetchone()[0]
        conn.commit()
        return True, uid
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def login_user(name, pwd):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, pwd FROM users WHERE name=%s", (name,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user and bcrypt.checkpw(pwd.encode(), user[3].encode()):
        return True, {"id": user[0], "name": user[1], "email": user[2]}
    return False, "Invalid credentials"