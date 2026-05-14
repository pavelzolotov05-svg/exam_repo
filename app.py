from flask import Flask, render_template, request, redirect, url_for, session, Response
import sqlalchemy
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Text, ForeignKey

app = Flask(__name__)
app.secret_key = "secret_kistet_kistum"

conn_string = "postgresql+psycopg2://postgres:122345@127.0.0.1:5432/postgres"
engine = sqlalchemy.create_engine(conn_string)


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False, default="user")  

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    payment_form = Column(String(100), nullable=True)
    status = Column(String(100), nullable=False, default="new")
    comment = Column(Text, nullable=True)

Base.metadata.create_all(engine)

def get_db():
    return SessionLocal()

def ensure_admin():
    db = get_db()
    try:
        admin = db.query(User).filter_by(username="admin").first()
        if not admin:
            admin = User(username="admin", password="password123", role="admin")
            db.add(admin)
            db.commit()
    finally:
        db.close()

ensure_admin()

def is_admin():
    return session.get("role") == "admin"

@app.route("/")
def index():
    return "Главная страница"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        try:
            user = db.query(User).filter_by(username=username, password=password).first()
            if user:
                session["user_id"] = user.id
                session["username"] = user.username
                session["role"] = user.role
                if user.role == "admin":
                    return redirect(url_for("admin_applications"))
                return redirect(url_for("user_page"))
            return "Неверный логин или пароль", 401
        finally:
            db.close()

    return render_template("login.html")

@app.route("/user")
def user_page():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return f"Страница пользователя: {session.get('username')}"

@app.route("/admin/applications")
def admin_applications():
    if not is_admin():
        return redirect(url_for("user_page"))

    db = get_db()
    try:
        apps = (
            db.query(Application, User, Course)
            .join(User, Application.user_id == User.id)
            .join(Course, Application.course_id == Course.id)
            .all()
        )
        return render_template("admin_applications.html", applications=apps)
    finally:
        db.close()

@app.route("/admin/applications/<int:app_id>/update", methods=["POST"])
def admin_update_application(app_id):
    if not is_admin():
        return redirect(url_for("user_page"))

    payment_form = request.form.get("payment_form")
    status = request.form.get("status")

    db = get_db()
    try:
        application = db.query(Application).filter_by(id=app_id).first()
        if not application:
            return "Заявка не найдена", 404

        application.payment_form = payment_form
        application.status = status
        db.commit()
        return redirect(url_for("admin_applications"))
    finally:
        db.close()

if __name__ == "__main__":
    app.run(debug=True)