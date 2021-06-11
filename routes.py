from app import app
from flask import redirect, render_template, request, session
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash
from db import db
from copy import copy

app.secret_key = getenv("SECRET_KEY")

@app.route("/")
def index():
    moderator = False
    try:
        username = session["username"]
        if db.session.execute("SELECT moderator FROM Users WHERE username=:username", {"username":username}).fetchone()[0] == 1:
            moderator = True
    except KeyError:
        pass
    return render_template("index.html", moderator= moderator)

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

@app.route("/work/<id>")
def work(id):
    sql = "SELECT * FROM Works WHERE id=:id"
    work = db.session.execute(sql, {"id":id}).fetchone()
    sql = "SELECT Users.username, Reviews.score, Reviews.id FROM Reviews, Users WHERE Reviews.work_id=:id AND Users.id = Reviews.user_id"
    reviews = db.session.execute(sql, {"id":work[0]}).fetchall()
    if reviews:
        sql = "SELECT AVG(score) FROM Reviews WHERE work_id=:id"
        score = round(db.session.execute(sql, {"id":work[0]}).fetchone()[0],1)
        if int(score) == score:
            score = int(score)
    else:
        score = "?"
    return render_template("work.html", work = work, reviews = reviews, score = score)

@app.route("/review/<id>")
def review(id):
    sql = "SELECT Works.name, Users.username, Reviews.score, Reviews.review FROM Reviews, Users, Works WHERE Reviews.id=:id AND Reviews.work_id = Works.id AND Reviews.user_id = Users.id"
    review = db.session.execute(sql, {"id":id}).fetchone()
    writer = False
    try:
        username = session["username"]
        if username == review[1]:
            writer = True
        else:
            moderator = db.session.execute("SELECT moderator FROM Users WHERE username=:username", {"username":username}).fetchone()[0]
            if moderator == 1:
                writer = True
    except KeyError:
        pass
    sql = "SELECT Users.username, Comments.writing, Comments.id FROM Users, Comments WHERE Comments.review_id=:id AND Comments.user_id = Users.id"
    comments = db.session.execute(sql, {"id":id}).fetchall()
    final_comments = []
    for comment in comments:
        sql = "SELECT Users.username, Replies.writing FROM Users, Replies WHERE Replies.comment_id=:id AND Replies.user_id = Users.id"
        replies = db.session.execute(sql, {"id":comment[2]}).fetchall()
        final_comments.append([comment[0],comment[1],comment[2],replies])
    return render_template("review.html", review = review, comments = final_comments, id = id, writer = writer)

@app.route("/review/<id>/<comment_id>")
def replies(id,comment_id):
    sql = "SELECT Users.username, Comments.writing FROM Users, Comments WHERE Comments.id=:id AND Comments.user_id = Users.id"
    comment = db.session.execute(sql, {"id":comment_id}).fetchone()
    sql = "SELECT Users.username, Replies.writing, Replies.id FROM Users, Replies WHERE Replies.comment_id=:id AND Replies.user_id = Users.id"
    replies = db.session.execute(sql, {"id":comment_id}).fetchall()
    return render_template("reply.html", id = id, comment_id = comment_id, comment = comment, replies = replies)

@app.route("/comment", methods=["POST"])
def comment():
    review_id = request.form["id"]
    username = session["username"]
    sql = "SELECT id FROM Users WHERE username=:username"
    user_id = db.session.execute(sql, {"username":username}).fetchone()[0]
    writing = request.form["comment"]
    sql = "INSERT INTO Comments (review_id, user_id, writing) VALUES (:review_id,:user_id,:writing)"
    db.session.execute(sql, {"review_id":review_id,"user_id":user_id,"writing":writing})
    db.session.commit()
    page = "/review/" + str(review_id)
    return redirect(page)

@app.route("/reply", methods=["POST"])
def reply():
    review_id = request.form["id"]
    comment_id = request.form["comment_id"]
    username = session["username"]
    sql = "SELECT id FROM Users WHERE username=:username"
    user_id = db.session.execute(sql, {"username":username}).fetchone()[0]
    writing = request.form["reply"]
    sql = "INSERT INTO Replies (comment_id, user_id, writing) VALUES (:comment_id,:user_id,:writing)"
    db.session.execute(sql, {"comment_id":comment_id,"user_id":user_id,"writing":writing})
    db.session.commit()
    page = "/review/" + str(review_id) + "/" + str(comment_id)
    return redirect(page)

@app.route("/edit/review/<id>")
def edit_review(id):
    review = db.session.execute("SELECT Reviews.id, review, score, username, work_id from Reviews, Users WHERE Reviews.id=:id AND Users.id = user_id", {"id":id}).fetchone()
    writer = False
    moderator = False
    try:
        username = session["username"]
        if username == review[3]:
            writer = 1
        mode = db.session.execute("SELECT moderator FROM Users WHERE username=:username", {"username":username}).fetchone()[0]
        if mode == 1:
            writer = 1
            moderator = 1
    except KeyError:
        pass
    return render_template("edit_review.html", moderator = moderator, writer = writer, review = review)

@app.route("/edit_review", methods=["POST"])
def delete_review():
    id = request.form["review_id"]
    work_id = request.form["work_id"]
    page = "/work/" + str(work_id)
    try:
        moderator = int(request.form["moderator"])
    except ValueError:
        moderator = False
    if moderator == 1:
        if int(request.form["delete_user"]) == 1:
            sql = "SELECT user_id FROM Reviews WHERE id=:id"
            user_id = db.session.execute(sql, {"id":id}).fetchone()[0]
            sql = "SELECT id from Reviews WHERE user_id=:user_id"
            reviews = db.session.execute(sql, {"user_id":user_id}).fetchall()
            
            sql = "DELETE FROM Reports USING Replies WHERE Replies.user_id=:user_id AND Reports.reply_id = Replies.id"
            db.session.execute(sql, {"user_id":user_id})
            sql = "DELETE FROM Reports USING Comments WHERE Comments.user_id=:user_id AND Reports.comment_id = Comments.id"
            db.session.execute(sql, {"user_id":user_id})
            sql = "DELETE FROM Reports USING Reviews WHERE Reviews.user_id=:user_id AND Reports.review_id = Reviews.id"
            db.session.execute(sql, {"user_id":user_id})

            sql = "DELETE FROM Replies WHERE user_id=:user_id"
            db.session.execute(sql, {"user_id":user_id})
            sql = "DELETE FROM Comments WHERE user_id=:user_id"
            db.session.execute(sql, {"user_id":user_id})

            for review in reviews:
                sql = "DELETE FROM Replies USING Comments WHERE Comments.review_id=:id AND Replies.comment_id = Comments.id"
                db.session.execute(sql, {"id":review[0]})
                sql = "DELETE FROM Comments WHERE review_id=:id"
                db.session.execute(sql, {"id":review[0]})
                sql = "DELETE FROM Reviews WHERE id=:id"
                db.session.execute(sql, {"id":review[0]})
            db.session.execute("DELETE FROM Users WHERE id=:id", {"id":user_id})
            db.session.commit()
            return redirect(page)

    if int(request.form["delete_review"]) == 1:
        sql = "DELETE FROM Reports USING Comments, Replies WHERE Comments.review_id=:id AND Replies.comment_id = Comments.id AND Reports.reply_id = Replies.id"
        db.session.execute(sql, {"id":id})
        sql = "DELETE FROM Replies USING Comments WHERE Comments.review_id=:id AND Replies.comment_id = Comments.id"
        db.session.execute(sql, {"id":id})
        sql = "DELETE FROM Reports USING Comments WHERE Comments.review_id=:id AND Reports.comment_id = Comments.id"
        db.session.execute(sql, {"id":id})
        sql = "DELETE FROM Comments WHERE review_id=:id"
        db.session.execute(sql, {"id":id})
        sql = "DELETE FROM Reports USING Reviews WHERE Reviews.id=:id AND Reports.review_id = Reviews.id"
        db.session.execute(sql, {"id":id})
        sql = "DELETE FROM Reviews WHERE id=:id"
        db.session.execute(sql, {"id":id})
        db.session.commit()
        return redirect(page)

    review = request.form["review"]
    if review:
        sql = "UPDATE Reviews SET review=:review WHERE id=:id"
        db.session.execute(sql, {"review":review, "id":id})

    score = request.form["score"]
    sql = "UPDATE Reviews SET score=:score WHERE id=:id"
    db.session.execute(sql, {"score":score, "id":id})

    db.session.commit()
    return redirect(page)

@app.route("/report/<type>/<id>")
def report(type,id):
    return render_template("report.html", type = type, id = id)

@app.route("/report", methods=["POST"])
def add_report():
    type = request.form["type"]
    id = request.form["id"]
    reason = request.form["reason"]
    page = "/"

    if type == "work":
        sql = "INSERT INTO Reports (work_id,report) VALUES (:id,:reason)"
        db.session.execute(sql, {"id":id, "reason":reason})
        page = "/work/"+str(id)

    if type == "review":
        sql = "SELECT user_id FROM Reviews WHERE id=:id"
        user_id = db.session.execute(sql,{"id":id}).fetchone()[0]
        sql = "INSERT INTO Reports (review_id,user_id,report) VALUES (:id,:user_id,:reason)"
        db.session.execute(sql, {"id":id, "user_id":user_id, "reason":reason})
        page = "/review/"+str(id)

    if type == "comment":
        sql = "SELECT user_id FROM Comments WHERE id=:id"
        user_id = db.session.execute(sql,{"id":id}).fetchone()[0]
        sql = "INSERT INTO Reports (comment_id,user_id,report) VALUES (:id,:user_id,:reason)"
        db.session.execute(sql, {"id":id, "user_id":user_id, "reason":reason})
        review_id = db.session.execute("SELECT review_id from Comments WHERE id=:id", {"id":id}).fetchone()[0]
        page = "/review/"+str(review_id)

    if type == "reply":
        sql = "SELECT user_id FROM Replies WHERE id=:id"
        user_id = db.session.execute(sql,{"id":id}).fetchone()[0]
        sql = "INSERT INTO Reports (reply_id,user_id,report) VALUES (:id,:user_id,:reason)"
        db.session.execute(sql, {"id":id, "user_id":user_id, "reason":reason})
        comment_id = db.session.execute("SELECT comment_id from Replies WHERE id=:id", {"id":id}).fetchone()[0]
        review_id = db.session.execute("SELECT review_id from Comments WHERE id=:id", {"id":comment_id}).fetchone()[0]
        page = "/review/"+str(review_id)+"/"+str(comment_id)

    if type == "user":
        sql = "INSERT INTO Reports (user_id,report) VALUES (:id,:reason)"
        db.session.execute(sql, {"id":id, "reason":reason})

    db.session.commit()
    return redirect(page)

@app.route("/reports")
def reports():
    work_reports = []
    review_reports = []
    comment_reports = []
    reply_reports = []
    user_reports = []
    reports = db.session.execute("SELECT * FROM Reports").fetchall()
    for report in reports:
        if report[0] != None:
            work_reports.append([f"/work/{report[0]}",report[5]])
        elif report[1] != None:
            review_reports.append([f"/review/{report[1]}",report[5]])
        elif report[2] != None:
            sql = "SELECT review_id FROM Comments WHERE id=:id"
            review_id = db.session.execute(sql, {"id":report[2]}).fetchone()[0]
            comment_reports.append([f"/review/{review_id}/{report[2]}",report[5]])
        elif report[3] != None:
            sql = "SELECT Comments.review_id, Comments.id FROM Comments, Replies WHERE Replies.id=:id AND Replies.comment_id = Comments.id"
            comment = db.session.execute(sql, {"id":report[3]}).fetchone()
            reply_reports.append([f"/review/{comment[0]}/{comment[1]}",report[5]])
        elif report[4] != None:
            pass
    
    return render_template("reports.html",work_reports=work_reports,review_reports=review_reports,comment_reports=comment_reports,reply_reports=reply_reports,user_reports=user_reports)
