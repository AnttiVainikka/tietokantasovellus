from flask import Flask
from flask import redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from os import getenv

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
db = SQLAlchemy(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/write")
def write():
    return render_template("write.html")

@app.route("/send", methods=["POST"])
def send():
    name = request.form["name"]
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
    db.session.execute("INSERT INTO Reviews (work_id, user_id, review, score) VALUES (:work_id, 1, :review, :score)", {"work_id":work_id,"review":review,"score":score})
    db.session.commit()
    return redirect("/")

