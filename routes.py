from app import app
from flask import redirect, render_template, request, session, abort
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash
import db
from functions import check_moderator, check_author, name_order
from copy import copy
from secrets import token_hex

app.secret_key = getenv("SECRET_KEY")

@app.route("/")
def index():
    moderator = check_moderator()
    return render_template("index.html", moderator= moderator)

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/log", methods=["POST"])
def log():
    username = request.form["username"]
    password = request.form["password"]
    hash_value = db.find_password(username)
    if hash_value != None:
        if check_password_hash(hash_value[0],password):
            session["username"] = username
            session["csrf_token"] = token_hex(16)
            return redirect("/")
    return redirect("/login")

@app.route("/logout")
def logout():
    del session["username"]
    del session["csrf_token"]
    return redirect("/")

@app.route("/create")
def create():
    return render_template("create.html",error=False)

@app.route("/create_account", methods=["POST"])
def create_account():
    username = request.form["username"]
    password = request.form["password"]
    password2 = request.form["password2"]

    user_id = db.find_user_id(username)
    if user_id != None:
        return render_template("create.html", error="Username taken")
    if password != password2:
        return render_template("create.html", error="Passwords not identical")

    password = generate_password_hash(password2)
    db.insert_user(username,password)
    return redirect("/login")

@app.route("/write")
def write():
    return render_template("write.html")

@app.route("/send", methods=["POST"])
def send():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    username = session["username"]
    user_id = db.find_user_id(username)
    name = request.form["name"]
    if not name:
        return redirect("/write")
    name = name.strip()
    type = request.form["type"]
    year = request.form["year"]
    language = request.form["language"]
    review = request.form["review"]
    score = request.form["score"]

    db.insert_review(name,type,year,language,review,score,user_id)
    return redirect("/")

@app.route("/search")
def search():
    return render_template("search.html")

@app.route("/result", methods=["POST"])
def result():
    name = request.form["name"]
    type = request.form["type"]
    year = request.form["year"]
    language = request.form["language"]
    results = db.find_results(name)

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

@app.route("/work/<id>")
def work(id):
    moderator = check_moderator()
    work = db.find_work(id)
    reviews = db.find_reviews(id)
    if reviews:
        score = round(db.find_average_score(id),1)
        if int(score) == score:
            score = int(score)
    else:
        score = "?"
    return render_template("work.html", work = work, reviews = reviews, score = score, moderator = moderator)

@app.route("/review/<id>")
def review(id):
    review = db.find_review(id)
    writer = check_author(review[1])
    moderator = check_moderator()
    if writer:
        moderator = False
    comments = db.find_comments(id)
    final_comments = []
    for comment in comments:
        replies = db.find_replies(comment[2])
        if check_author(comment[0]):
            final_comments.append([comment[0],comment[1],comment[2],replies,True])
        else:
            final_comments.append([comment[0],comment[1],comment[2],replies,False])
    return render_template("review.html", review = review, comments = final_comments, id = id, writer = writer, moderator = moderator)

@app.route("/review/<id>/<comment_id>")
def replies(id,comment_id):
    comment = db.find_comment(comment_id)
    replies = db.find_replies(comment_id)
    final_replies = []
    for reply in replies:
        if check_author(reply[0]):
            final_replies.append([reply[0],reply[1],reply[2],True])
        else:
            final_replies.append([reply[0],reply[1],reply[2],False])
    return render_template("reply.html", id = id, comment_id = comment_id, comment = comment, replies = final_replies)

@app.route("/comment", methods=["POST"])
def comment():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    review_id = request.form["id"]
    username = session["username"]
    user_id = db.find_user_id(username)
    writing = request.form["comment"]
    db.insert_comment(review_id,user_id,writing)
    page = "/review/" + str(review_id)
    return redirect(page)

@app.route("/reply", methods=["POST"])
def reply():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    review_id = request.form["id"]
    comment_id = request.form["comment_id"]
    username = session["username"]
    user_id = db.find_user_id(username)
    writing = request.form["reply"]
    db.insert_reply(comment_id,user_id,writing)
    page = "/review/" + str(review_id) + "/" + str(comment_id)
    return redirect(page)

@app.route("/edit/work/<id>")
def edit_work(id):
    moderator = check_moderator()
    work = db.find_work(id)
    return render_template("edit_work.html", moderator=moderator, work=work)

@app.route("/edit_work", methods=["POST"])
def edit_work_properties():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    work_id = request.form["work_id"]
    if request.form["delete"] == "1":
        db.delete_work(work_id)
        return redirect("/")

    name = request.form["name"]
    type = request.form["type"]
    year = request.form["year"]
    language = request.form["language"]

    if name:
        db.update_work_name(work_id,name)
    db.update_work_properties(work_id,type,year,language)

    page = "/work/"+str(work_id)
    return redirect(page)

@app.route("/edit/review/<id>")
def edit_review(id):
    review = db.find_review_edit(id)
    writer = check_author(review[3])
    moderator = check_moderator()
    if writer:
        moderator = False
    return render_template("edit_review.html", moderator = moderator, writer = writer, review = review)

@app.route("/edit_review", methods=["POST"])
def edit_own_review():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    id = request.form["review_id"]
    work_id = request.form["work_id"]
    page = "/work/" + str(work_id)

    if int(request.form["delete_review"]) == 1:
        db.delete_review(id)
        return redirect(page)

    review = request.form["review"]
    if review:
        db.update_review(id,review)

    score = request.form["score"]
    db.update_score(id,score)

    return redirect(page)

@app.route("/moderate_review", methods=["POST"])
def moderate_review():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    id = request.form["review_id"]
    if int(request.form["delete"]) == 1:
        user_id = db.find_review_author(id)
        db.delete_user(user_id)
        return redirect("/reports")

    if int(request.form["delete"]) == 2:
        db.delete_review(id)

    return redirect("/reports")

@app.route("/edit/comment/<id>")
def edit_comment(id):
    moderator = check_moderator()
    comment = db.find_comment_edit(id)
    writer = check_author(comment[0])
    if writer:
        moderator = False
    return render_template("edit_comment.html", moderator=moderator, comment=comment, id=id, writer=writer)

@app.route("/edit_comment", methods=["POST"])
def edit_own_comment():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    comment_id = request.form["comment_id"]
    review_id = request.form["review_id"]
    page = "/review/" + str(review_id)
    if request.form["delete"] == "1":
        db.delete_comment(comment_id)
        return redirect(page)
    writing = request.form["writing"]
    if writing:
        db.update_comment(comment_id,writing)
    return redirect(page)

@app.route("/moderate_comment", methods=["POST"])
def moderate_comment():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    comment_id = request.form["comment_id"]

    if request.form["delete"] == "2":
        user_id = db.find_comment_author(comment_id)
        db.delete_user(user_id)
        return redirect("/reports")

    if request.form["delete"] == "1":
        db.delete_comment(comment_id)

    return redirect("/reports")

@app.route("/edit/reply/<id>")
def edit_reply(id):
    moderator = check_moderator()
    reply = db.find_reply(id)
    writer = check_author(reply[0])
    if writer:
        moderator = False
    return render_template("edit_reply.html", moderator=moderator, reply=reply, id=id, writer=writer)

@app.route("/edit_reply", methods=["POST"])
def edit_own_reply():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    reply_id = request.form["reply_id"]
    path = db.find_comment_path(reply_id)
    page = "/review/" + str(path[0]) + "/" + str(path[1])
    if request.form["delete"] == "1":
        db.delete_reply(reply_id)
        return redirect(page)
    writing = request.form["writing"]
    if writing:
        db.update_reply(reply_id,writing)
    return redirect(page)

@app.route("/moderate_reply", methods=["POST"])
def moderate_reply():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    reply_id = request.form["reply_id"]

    if request.form["delete"] == "2":
        user_id = db.find_reply_author(reply_id)
        db.delete_user(user_id)
        return redirect("/reports")

    if request.form["delete"] == "1":
        db.delete_reply(reply_id)

    return redirect("/reports")

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
        db.insert_work_report(id,reason)
        page = "/work/"+str(id)

    if type == "review":
        db.insert_review_report(id,reason)
        page = "/review/"+str(id)

    if type == "comment":
        review_id = db.insert_comment_report(id,reason)
        page = "/review/"+str(review_id)

    if type == "reply":
        id = db.insert_reply_report(id,reason)
        page = "/review/"+str(id[0])+"/"+str(id[1])

    return redirect(page)

@app.route("/reports")
def reports():
    work_reports = []
    review_reports = []
    comment_reports = []
    reply_reports = []
    reports = db.find_reports()
    moderator = check_moderator()

    for report in reports:
        if report[0] != None:
            work_reports.append([f"/work/{report[0]}",report[5]])
        elif report[1] != None:
            review_reports.append([f"/review/{report[1]}",report[5]])
        elif report[2] != None:
            comment_reports.append([f"/edit/comment/{report[2]}",report[5]])
        elif report[3] != None:
            reply_reports.append([f"/edit/reply/{report[3]}",report[5]])

    return render_template("reports.html",work_reports=work_reports,review_reports=review_reports,comment_reports=comment_reports,reply_reports=reply_reports,moderator=moderator)
