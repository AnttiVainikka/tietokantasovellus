from flask import Flask
from flask import redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash
from copy import copy

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
    name = name.strip()
    type = request.form["type"]
    year = request.form["year"]
    language = request.form["language"]
    review = request.form["review"]
    score = request.form["score"]
    sql = "SELECT id FROM Works WHERE LOWER(name)=:name AND type=:type"
    id = db.session.execute(sql, {"name":name.lower(), "type":type}).fetchone()
    if id == None:
        sql = "INSERT INTO Works (name, type, year, language) VALUES (:name,:type,:year,:language) RETURNING id"
        id = db.session.execute(sql, {"name":name,"type":type,"year":year,"language":language}).fetchone()
    work_id = id[0]
    db.session.execute("INSERT INTO Reviews (work_id, user_id, review, score) VALUES (:work_id, :user_id, :review, :score)", {"work_id":work_id,"user_id":user_id,"review":review,"score":score})
    db.session.commit()
    return redirect("/")

@app.route("/search")
def search():
    return render_template("search.html")


@app.route("/result", methods=["POST"])
def result():
    name = request.form["name"]
    if not name:
        results = db.session.execute("SELECT * FROM Works").fetchall()
    else:
        name = name.strip()
        sql = "SELECT * FROM Works WHERE LOWER(name) LIKE :name"
        results = db.session.execute(sql, {"name":"%"+name.lower()+"%"}).fetchall()
    if results == None:
        return redirect("/")
    type = request.form["type"]
    year = request.form["year"]
    language = request.form["language"]
    final_results = copy(results)
    for result in results:
        if type != "Any":
            if result[2] != type:
                final_results.remove(result)
                continue
        if year != "Any":
            if result[3] != int(year):
                final_results.remove(result)
                continue
        if language != "Any":
            if result[4] != language:
                final_results.remove(result)
    final_results.sort(key=name_order)
    return render_template("results.html", results = final_results)

def name_order(work):
    return work[1].lower()

@app.route("/work/<name>")
def work(name):
    sql = "SELECT * FROM Works WHERE name=:name"
    work = db.session.execute(sql, {"name":name}).fetchone()
    sql = "SELECT Users.username, Reviews.score, Reviews.review FROM Reviews, Users WHERE Reviews.work_id=:id AND Users.id = Reviews.user_id"
    reviews = db.session.execute(sql, {"id":work[0]}).fetchall()
    if reviews:
        sql = "SELECT AVG(score) FROM Reviews WHERE work_id=:id"
        score = round(db.session.execute(sql, {"id":work[0]}).fetchone()[0],1)
        if int(score) == score:
            score = int(score)
    else:
        score = "?"
    return render_template("work.html", work = work, reviews = reviews, score = score)
