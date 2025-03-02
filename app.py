from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_bcrypt import Bcrypt
from functools import wraps
import random
import string
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'linh_duyen_04'
bcrypt = Bcrypt(app)
DATABASE = 'database.db'

# Khởi tạo database
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY NOT NULL UNIQUE,
            username TEXT NOT NULL UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user',
            is_blocked INTEGER DEFAULT 0
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS posts (
            post_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            title TEXT,
            content TEXT,
            image_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(username) REFERENCES users(username)
        )''')
        conn.commit()

init_db()

# Form đăng ký
class RegisterForm(FlaskForm):
    user_id = StringField("User ID", validators=[DataRequired(), Length(min=9, max=12)])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Xác nhận Password', validators=[DataRequired(), EqualTo('password')])
    admin_code = StringField('Admin Code')
    submit = SubmitField('Register')

# Form đăng nhập
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@app.route('/')
def home():
    return render_template('home.html')

# Hàm riêng để xác định role
def determine_role(admin_code):
    """Xác định role dựa trên admin_code."""
    if admin_code == 'LD04-0225':
        return 'admin'
    return 'user'

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        username = form.username.data
        password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        admin_code = form.admin_code.data

        role = determine_role(admin_code)
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (user_id, username, password, role) VALUES (?, ?, ?, ?)",
                          (user_id, username, password, role))
                conn.commit()
                flash("Tạo tài khoản thành công!", "success")
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash("Id người dùng đã tồn tại!", "danger")
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT password, role, is_blocked FROM users WHERE username = ?", (username,))
            user = c.fetchone()
            if user and bcrypt.check_password_hash(user[0], password):
                if user[2]:
                    flash("Tài khoản của bạn đã bị khóa!", "danger")
                    return redirect(url_for('login'))
                session['username'] = username
                session['role'] = user[1]
                return redirect(url_for('dashboard'))
            else:
                flash("Tên người dùng hoặc mật khẩu không hợp lệ!", "danger")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Phân trang cho user_posts
    page_user = request.args.get('page_user', 1, type=int)
    per_page = 9  # 9 bài mỗi trang
    offset_user = (page_user - 1) * per_page

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        # Tổng số bài viết của người dùng hiện tại
        c.execute("SELECT COUNT(*) FROM posts WHERE username = ?", (session['username'],))
        total_user_posts = c.fetchone()[0]
        total_user_pages = (total_user_posts + per_page - 1) // per_page

        # Lấy bài viết của người dùng hiện tại
        c.execute("SELECT post_id, title, content, image_url FROM posts WHERE username = ? ORDER BY post_id DESC LIMIT ? OFFSET ?",
                  (session['username'], per_page, offset_user))
        user_posts = c.fetchall()

        # Phân trang cho other_posts
        page_other = request.args.get('page_other', 1, type=int)
        offset_other = (page_other - 1) * per_page

        # Tổng số bài viết của người dùng khác
        c.execute("SELECT COUNT(*) FROM posts WHERE username != ?", (session['username'],))
        total_other_posts = c.fetchone()[0]
        total_other_pages = (total_other_posts + per_page - 1) // per_page

        # Lấy bài viết của người dùng khác
        c.execute(
            "SELECT post_id, username, title, content, image_url FROM posts WHERE username != ? ORDER BY post_id DESC LIMIT ? OFFSET ?",
            (session['username'], per_page, offset_other))
        other_posts = c.fetchall()

    return render_template('dashboard.html',
                           user_posts=user_posts,
                           other_posts=other_posts,
                           page_user=page_user,
                           total_user_pages=total_user_pages,
                           page_other=page_other,
                           total_other_pages=total_other_pages)

@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        flash("Truy cập trái phép!", "danger")
        return redirect(url_for('home'))

    # Phân trang cho admin
    page_admin = request.args.get('page_admin', 1, type=int)
    per_page = 10  # 10 user mỗi trang
    offset_user = (page_admin - 1) * per_page
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        # Tổng số bài viết của người dùng hiện tại
        c.execute("SELECT COUNT(*) FROM posts WHERE username != ?", (session['username'],))
        total_user_posts = c.fetchone()[0]
        total_user_pages = (total_user_posts + per_page - 1) // per_page

        c.execute("SELECT * FROM users WHERE username != ? ORDER BY user_id DESC LIMIT ? OFFSET ?",
                  (session['username'], per_page, offset_user))
        users = c.fetchall()
    return render_template('admin.html', users=users,
                           page_admin=page_admin,
                           total_user_pages=total_user_pages,)

@app.route('/create_post', methods=['POST'])
def create_post():
    if 'username' not in session:
        flash("Vui lòng đăng nhập!", "warning")
        return redirect(url_for('login'))
    title = request.form.get('title')
    content = request.form.get('content')
    image = request.files.get('image')  # Lấy file ảnh
    image_url = None
    if image:
        image_url = f"/static/uploads/{image.filename}"
        image.save(f"static/uploads/{image.filename}")  # Lưu ảnh vào thư mục static/uploads
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO posts (username, title, content, image_url) VALUES (?, ?, ?, ?)",
                      (session['username'], title, content, image_url))
            conn.commit()
        flash("Đã đăng tải bài viếtviết!", "success")
    except sqlite3.Error as e:
        flash(f"Error: {e}", "danger")
    return redirect(url_for('dashboard'))

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'username' not in session:
        flash("Vui lòng đăng nhập!", "warning")
        return redirect(url_for('login'))

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT content FROM posts WHERE post_id=?", (post_id,))
        post = c.fetchone()

    if post and session['username'] == post[0]:
        if request.method == 'POST':
            new_content = request.form.get('content')
            with sqlite3.connect(DATABASE) as conn:
                c = conn.cursor()
                c.execute("UPDATE posts SET content=? WHERE post_id=?", (new_content, post_id))
                conn.commit()
            flash("Bài viết đã cập nhật thành côngcông!", "success")
            return redirect(url_for('dashboard'))
        return render_template('edit_post.html', post=post)
    flash("Hành động trái phépphép!", "danger")
    return redirect(url_for('dashboard'))

@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    if 'username' not in session:
        flash("Vui lòng đăng nhập!", "warning")
        return redirect(url_for('login'))
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM posts WHERE post_id=? AND user=?", (post_id, session['username']))
        conn.commit()
    flash("Xóa bài viết thành công!", "success")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for('home'))

# Decorator kiểm tra quyền admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("Truy cập trái phép!", "danger")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# API khóa/mở khóa user
def toggle_block_user(username):
    if session.get('role') == 'admin':
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT is_blocked FROM users WHERE username=?", (username,))
            user = c.fetchone()
            if user:
                new_status = 0 if user[0] else 1
                c.execute("UPDATE users SET is_blocked=? WHERE username=?", (new_status, username))
                conn.commit()
                status_text = "unblocked" if new_status == 0 else "blocked"
                flash(f"User {status_text} successfully!", "success")
    return redirect(url_for('admin'))

@app.route('/block_user/<username>')
@admin_required
def block_user(username):
    return toggle_block_user(username)

@app.route('/unblock_user/<username>')
@admin_required
def unblock_user(username):
    return toggle_block_user(username)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form.get('username')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash("Mật khẩu không khớp!", "danger")
            return redirect(url_for('reset_password'))

        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=?", (username,))
            user = c.fetchone()

            if user:
                hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                c.execute("UPDATE users SET password=? WHERE username=?", (hashed_password, username))
                conn.commit()
                flash("Đặt lại mật khẩu thành công!", "success")
                return redirect(url_for('login'))
            else:
                flash("Tên người dùng không tồn tại!", "danger")

    return render_template('reset_password.html')

if __name__ == "__main__":
    app.run(debug=True)