import psycopg2
import bcrypt

DB_URL = ""
def get_conn():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            pwd VARCHAR(255) NOT NULL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
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