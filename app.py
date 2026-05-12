from flask import Flask, render_template, request, Response, redirect, url_for
import sqlalchemy
from sqlalchemy import text
from sqlalchemy.engine import URL
import os

app = Flask(import_name=__name__, template_folder=os.getcwd())
conn_string = "postgresql+psycopg2://postgres:122345@127.0.0.1:5432/postgres"
engine = sqlalchemy.create_engine(conn_string)

ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "password123"

def check_auth(username, password):
    return username == ADMIN_LOGIN and password == ADMIN_PASSWORD

def authenticate():
    return Response(
        "Необходима авторизация",
        401,
        {"WWW-Authenticate": 'Basic realm="Admin Panel"'},
    )

@app.route("/admin")
def admin_panel():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    try:
        with engine.connect() as conn:
            query = text("SELECT id, user_id, course_name, status FROM zadacha ORDER BY id")
            result = conn.execute(query)
            applications = [dict(row._mapping) for row in result]
            
        return render_template("admin.html", applications=applications)
    except Exception as e:
        return f"Ошибка базы данных: {e}"
    
@app.route("/update_status", methods=["POST"])
def update_status():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    app_id = request.form.get("app_id")
    new_status = request.form.get("status")

    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE zadacha SET status = :status WHERE id = :id"),
                {"status": new_status, "id": app_id}
            )
        return redirect(url_for("admin"))
    except Exception as e:
        return f"Ошибка при обновлении: {e}"

if __name__ == "__main__":
    app.run(debug=True)