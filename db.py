import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="FinSight",
    user="postgres",
    password="Shravani",   # Use your PostgreSQL password
    port="5432"
)

cursor = conn.cursor()

print("Database connected successfully")