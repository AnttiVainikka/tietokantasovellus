from flask import Flask
from flask import redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.secret_key = getenv("SECRET_KEY")
db = SQLAlchemy(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/log", methods=["POST"])
def log():
    username = request.form["username"]
    password = request.form["password"]
    sql = "SELECT password FROM Users WHERE username=:username"
    hash_value = db.session.execute(sql, {"username":username}).fetchone()
    if hash_value != None:
        if check_password_hash(hash_value[0],password):
            session["username"] = username
            return redirect("/")
    return redirect("/login")

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

@app.route("/create")
def create():
    return render_template("create.html",error=False)

@app.route("/create_account", methods=["POST"])
def create_account():
    username = request.form["username"]
    password = request.form["password"]
    password2 = request.form["password2"]
    sql = "SELECT id FROM Users WHERE username=:username"
    user = db.session.execute(sql, {"username":username}).fetchone()
    if user != None:
        return render_template("create.html", error="Username taken")
    if password != password2:
        return render_template("create.html", error="Passwords not identical")
    password = generate_password_hash(password2)
    db.session.execute("INSERT INTO Users (username, moderator, password) VALUES (:username, 0, :password)", {"username":username,"password":password})
    db.session.commit()
    return redirect("/login")

@app.route("/write")
def write():
    return render_template("write.html")

@app.route("/send", methods=["POST"])
def send():
    try:
        username = session["username"]
    except KeyError:
        return redirect("/write")
    sql = "SELECT id FROM Users WHERE username=:username"
    user_id = db.session.execute(sql, {"username":username}).fetchone()[0]
    name = request.form["name"]
    if not name:
        return redirect("/write")
    type = request.form["type"]
    year = request.form["year"]
    language = request.form["language"]
    review = request.form["review"]
    score = request.form["score"]
    sql = "SELECT id FROM Works WHERE name=:name AND type=:type"
    id = db.session.execute(sql, {"name":name,"type":type}).fetchone()
    if id == None:
        sql = "INSERT INTO Works (name, type, year, language) VALUES (:name,:type,:year,:language) RETURNING id"
        id = db.session.execute(sql, {"name":name,"type":type,"year":year,"language":language}).fetchone()
    work_id = id[0]
    db.session.execute("INSERT INTO Reviews (work_id, user_id, review, score) VALUES (:work_id, :user_id, :review, :score)", {"work_id":work_id,"user_id":user_id,"review":review,"score":score})
    db.session.commit()
    return redirect("/")

