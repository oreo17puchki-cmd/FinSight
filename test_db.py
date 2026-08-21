import os
import psycopg2

def test():
    try:
        conn = psycopg2.connect(
            host="db.traottjhbupauinzlxkj.supabase.co",
            database="postgres",
            user="postgres",
            password="Finsight@info",
            port=6543,
            connect_timeout=10
        )
        print("Connected successfully with Finsight@info on port 6543!")
        conn.close()
    except Exception as e:
        print(f"Failed with Finsight@info: {e}")
        
    try:
        conn = psycopg2.connect(
            host="db.traottjhbupauinzlxkj.supabase.co",
            database="postgres",
            user="postgres",
            password="[Finsight@info]",
            port=6543,
            connect_timeout=10
        )
        print("Connected successfully with [Finsight@info] on port 6543!")
        conn.close()
    except Exception as e:
        print(f"Failed with [Finsight@info]: {e}")

if __name__ == "__main__":
    test()
