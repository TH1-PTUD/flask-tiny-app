from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.config["SECRET_KEY"] = "linh_duyen_04"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
admin = Admin(app, name="Trang Quản Trị", template_mode="bootstrap3")

# Tạo bảng User trong database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

# Tạo bảng Blog trong database
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

# Thêm trang Admin
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Blog, db.session))

# Form đăng ký
class RegisterForm(FlaskForm):
    username = StringField("Tên đăng nhập", validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField("Mật khẩu", validators=[DataRequired(), Length(min=6, max=20)])
    confirm_password = PasswordField("Nhập lại mật khẩu", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Đăng ký")

# Form đăng nhập
class LoginForm(FlaskForm):
    username = StringField("Tên đăng nhập", validators=[DataRequired()])
    password = PasswordField("Mật khẩu", validators=[DataRequired()])
    submit = SubmitField("Đăng nhập")

# Form thêm bài viết
class BlogForm(FlaskForm):
    title = StringField("Tiêu đề", validators=[DataRequired(), Length(min=3, max=100)])
    content = TextAreaField("Nội dung", validators=[DataRequired()])
    submit = SubmitField("Đăng bài")

@app.route("/")
def home():
    if "user" not in session:
        flash("Vui lòng đăng nhập để xem bài viết.", "warning")
        return redirect(url_for("login"))
    blogs = Blog.query.all()
    return render_template("index.html", blogs=blogs)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Tên đăng nhập đã tồn tại!", "danger")
        else:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            session["user"] = user.username
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for("home"))
        else:
            flash("Sai tên đăng nhập hoặc mật khẩu!", "danger")
    return render_template("login.html", form=form)

@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", username=session["user"])
    flash("Vui lòng đăng nhập!", "warning")
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for("home"))

@app.route("/admin")
def admin_redirect():
    return redirect("/admin/")

# Route thêm bài viết
@app.route("/add_blog", methods=["GET", "POST"])
def add_blog():
    if "user" not in session:
        flash("Bạn cần đăng nhập để thêm bài viết.", "warning")
        return redirect(url_for("login"))

    form = BlogForm()
    if form.validate_on_submit():
        new_blog = Blog(title=form.title.data, content=form.content.data)
        db.session.add(new_blog)
        db.session.commit()
        flash("Bài viết đã được đăng!", "success")
        return redirect(url_for("home"))

    return render_template("add_blog.html", form=form)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Tạo database nếu chưa có
    app.run(host="0.0.0.0", port=5000, debug=True)
