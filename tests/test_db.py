import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "zakascore.db")
 
 
def test_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
 
    print(f"Connected to database at: {DB_PATH}\n")
 
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall() 
 
    
    if not tables:
        print("No tables found. Did you run init_db.py first?")
    else:
        print("Tables found in the database:")
        for table in tables:
            print(f" - {table[0]}")
 
   
    conn.close()
 
if __name__ == "__main__":
    test_database()