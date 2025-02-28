from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_bcrypt import Bcrypt
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
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT DEFAULT 'user',
            is_blocked INTEGER DEFAULT 0
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            content TEXT,
            FOREIGN KEY(user) REFERENCES users(username)
        )''')
        conn.commit()

init_db()

# Form đăng ký
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

# Form đăng nhập
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                flash("Account created successfully!", "success")
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash("Username already exists!", "danger")
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT password, role, is_blocked FROM users WHERE username=?", (username,))
            user = c.fetchone()
            if user and bcrypt.check_password_hash(user[0], password):
                if user[2]:
                    flash("Your account has been blocked!", "danger")
                    return redirect(url_for('login'))
                session['username'] = username
                session['role'] = user[1]
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid username or password!", "danger")
    return render_template('login.html', form=form)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'username' in session:
        # Lấy tất cả bài viết của người dùng hiện tại
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT id, content FROM posts WHERE user_id=?", (session['username'],))
            user_posts = c.fetchall()

            # Lấy tất cả bài viết của người dùng khác
            c.execute("SELECT id, user_id, content FROM posts WHERE user_id != ?", (session['username'],))
            other_posts = c.fetchall()

        return render_template('dashboard.html', username=session['username'], user_posts=user_posts, other_posts=other_posts)
    
    flash("Please log in first!", "warning")
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT username, is_blocked FROM users")
        users = c.fetchall()
    return render_template('admin.html', users=users)

@app.route('/block_user/<username>')
def block_user(username):
    if session.get('role') == 'admin':
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET is_blocked=1 WHERE username=?", (username,))
            conn.commit()
        flash("User blocked successfully!", "success")
    return redirect(url_for('admin'))

@app.route('/reset_password/<username>')
def reset_password(username):
    if session.get('role') == 'admin':
        new_password = bcrypt.generate_password_hash("default123").decode('utf-8')
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
            conn.commit()
        flash("Password reset successfully!", "success")
    return redirect(url_for('admin'))

@app.route('/create_post', methods=['POST'])
def create_post():
    if 'username' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))
    content = request.form.get('content')
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO posts (user, content) VALUES (?, ?)", (session['username'], content))
        conn.commit()
    flash("Post created successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'username' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))
    
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT content FROM posts WHERE id=?", (post_id,))
        post = c.fetchone()

    if post and session['username'] == post[0]:
        if request.method == 'POST':
            new_content = request.form.get('content')
            with sqlite3.connect(DATABASE) as conn:
                c = conn.cursor()
                c.execute("UPDATE posts SET content=? WHERE id=?", (new_content, post_id))
                conn.commit()
            flash("Post updated successfully!", "success")
            return redirect(url_for('dashboard'))
        return render_template('edit_post.html', post=post)
    flash("Unauthorized action!", "danger")
    return redirect(url_for('dashboard'))

@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    if 'username' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM posts WHERE id=? AND user=?", (post_id, session['username']))
        conn.commit()
    flash("Post deleted successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
    