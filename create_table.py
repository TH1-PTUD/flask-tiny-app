import sqlite3

# Kết nối tới cơ sở dữ liệu
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Thêm cột is_blocked (kiểu BOOLEAN) vào bảng (giả sử bảng có tên 'users')
cursor.execute('''
    ALTER TABLE users
    ADD COLUMN is_blocked BOOLEAN DEFAULT 0;
''')

# Commit thay đổi và đóng kết nối
conn.commit()
conn.close()

print("Cột 'is_blocked' đã được thêm vào bảng.")
