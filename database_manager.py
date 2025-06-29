import sqlite3
from typing import List, Tuple, Optional, Union

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self) -> None: # Create table if it does not exist
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS entries (
                    ID TEXT,
                    TYPE TEXT,
                    VALUE TEXT
                )
            ''')
            conn.commit()
    
    def add(self, id: str, type: str, value: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO entries (ID, TYPE, VALUE) VALUES (?, ?, ?)",
                    (id, type, value)
                )
                conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"db error: {e}")
            return False
    
    def list_all(self) -> List[Tuple[str, str, str]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ID, TYPE, VALUE FROM entries")
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"db error: {e}")
            return []
    
    def search_by_id(self, id: str) -> List[Tuple[str, str, str]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ID, TYPE, VALUE FROM entries WHERE ID = ?",
                    (id,)
                )
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"db error: {e}")
            return []
    
    def search_by_type(self, type: str) -> List[Tuple[str, str, str]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ID, TYPE, VALUE FROM entries WHERE TYPE = ?",
                    (type,)
                )
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
    
    def search(self, search_term: str, search_by: str = "id") -> List[Tuple[str, str, str]]:
        if search_by.lower() == "id":
            return self.search_by_id(search_term)
        elif search_by.lower() == "type":
            return self.search_by_type(search_term)
        else:
            print(f"Invalid search_by parameter: {search_by}. Use 'id' or 'type'.")
            return []

def add(id: str, type: str, value: str, db_path: str) -> bool:
    db = DatabaseManager(db_path)
    return db.add(id, type, value)

def list_all(db_path: str) -> List[Tuple[str, str, str]]:
    db = DatabaseManager(db_path)
    return db.list_all()

def search(search_term: str, db_path: str, search_by: str = "id") -> List[Tuple[str, str, str]]:
    db = DatabaseManager(db_path)
    return db.search(search_term, search_by)

if __name__ == "__main__":
    pass