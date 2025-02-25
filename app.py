from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_bcrypt import Bcrypt
import json

app = Flask(__name__)
app.config["SECRET_KEY"] = "linh_duyen_04"  
bcrypt = Bcrypt(app)

# Lưu thông tin người dùng tạm thời
users = {}

# load dữ liệu blog từ file Json
with open("./static/blogs_data.json", "r", encoding="utf-8") as file:
    blogs = json.load(file)


# Form đăng ký
class RegisterForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=20)]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=6, max=20)]
    )
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")


# Form đăng nhập
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


# @app.route("/")
# def home():
#     # luôn truyền biến blogs để hiển thị nội dung blog ở trang chủ
#     return render_template("base.html", blogs=blogs)


@app.route("/")
def home():
    # Kiểm tra đăng nhập
    if "user" not in session:
        flash("Please log in to view the blog posts.", "warning")
        return redirect(url_for("login"))

    # Số bài trên mỗi trang
    per_page = 9
    # Lấy số trang từ query string, mặc định là 1 nếu không có
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1

    # Tính chỉ số bắt đầu và kết thúc
    start = (page - 1) * per_page
    end = start + per_page

    # Lấy danh sách blog của trang hiện tại
    current_blogs = blogs[start:end]

    # Tính tổng số trang
    total_pages = (len(blogs) + per_page - 1) // per_page

    return render_template(
        "base.html", blogs=current_blogs, page=page, total_pages=total_pages
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        if username in users:
            flash("Username already exists!", "danger")
        else:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
                "utf-8"
            )
            users[username] = hashed_password
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if username in users and bcrypt.check_password_hash(users[username], password):
            session["user"] = username
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password!", "danger")
    return render_template("login.html", form=form)


@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", username=session["user"], blogs=blogs)
    flash("Please log in first!", "warning")
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
