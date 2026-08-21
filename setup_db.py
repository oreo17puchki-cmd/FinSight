import os
import sys

from db import get_connection, ensure_transactions_table
from database.migrate_investments import apply_investment_migration

def setup_db():
    print("Executing schema.sql...")
    with get_connection() as conn:
        with conn.cursor() as cursor:
            schema_path = os.path.join("database", "schema.sql")
            with open(schema_path, "r", encoding="utf-8") as f:
                cursor.execute(f.read())
    
    print("Ensuring transactions table...")
    ensure_transactions_table()
    
    print("Applying migrations...")
    apply_investment_migration()
    
    print("Database setup complete!")

if __name__ == "__main__":
    setup_db()
