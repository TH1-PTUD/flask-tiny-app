import sqlite3

# Đường dẫn đến file database.db
DATABASE = "database.db"

def add_created_at_column():
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            
            # Kiểm tra xem cột created_at đã tồn tại chưa
            c.execute("PRAGMA table_info(posts)")
            columns = [col[1] for col in c.fetchall()]
            
            if 'created_at' not in columns:
                # Thêm cột created_at nếu chưa tồn tại
                c.execute("ALTER TABLE posts ADD COLUMN created_at TEXT")
                print("Added created_at column to posts table successfully!")
            else:
                print("created_at column already exists in posts table!")
                
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")

if __name__ == "__main__":
    add_created_at_column()