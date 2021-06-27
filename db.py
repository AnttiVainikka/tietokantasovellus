from app import app
from flask_sqlalchemy import SQLAlchemy
from os import getenv


app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
db = SQLAlchemy(app)

def find_user_id(username):
    sql = "SELECT id FROM Users WHERE username=:username"
    try:
        return db.session.execute(sql, {"username":username}).fetchone()[0]
    except:
        return None

def find_moderator(username):
    sql = "SELECT moderator FROM Users WHERE username=:username"
    return db.session.execute(sql, {"username":username}).fetchone()[0]

def find_password(username):
    sql = "SELECT password FROM Users WHERE username=:username"
    return db.session.execute(sql, {"username":username}).fetchone()

def find_results(name):
    if not name:
        results = db.session.execute("SELECT * FROM Works").fetchall()
    else:
        name = name.strip()
        sql = "SELECT * FROM Works WHERE LOWER(name) LIKE :name"
        results = db.session.execute(sql, {"name":"%"+name.lower()+"%"}).fetchall()
    return results

def find_work(id):
    sql = "SELECT * FROM Works WHERE id=:id"
    return db.session.execute(sql, {"id":id}).fetchone()

def find_reviews(id):
    sql = "SELECT Users.username, Reviews.score, Reviews.id FROM Reviews, Users WHERE Reviews.work_id=:id AND Users.id = Reviews.user_id"
    return db.session.execute(sql, {"id":id}).fetchall()

def find_review(id):
    sql = "SELECT Works.name, Users.username, Reviews.score, Reviews.review, Works.id FROM Reviews, Users, Works WHERE Reviews.id=:id AND Reviews.work_id = Works.id AND Reviews.user_id = Users.id"
    return db.session.execute(sql, {"id":id}).fetchone()

def find_review_edit(id):
    sql = "SELECT Reviews.id, review, score, username, work_id from Reviews, Users WHERE Reviews.id=:id AND Users.id = user_id"
    return db.session.execute(sql, {"id":id}).fetchone()

def find_review_author(id):
    sql = "SELECT user_id FROM Reviews WHERE id=:id"
    return db.session.execute(sql, {"id":id}).fetchone()[0]

def find_comment_author(id):
    sql = "SELECT user_id FROM Comments WHERE id=:id"
    return db.session.execute(sql, {"id":id}).fetchone()[0]

def find_reply_author(id):
    sql = "SELECT user_id FROM Replies WHERE id=:id"
    return db.session.execute(sql, {"id":id}).fetchone()[0]

def find_average_score(id):
    sql = "SELECT AVG(score) FROM Reviews WHERE work_id=:id"
    return db.session.execute(sql, {"id":id}).fetchone()[0]

def find_comments(id):
    sql = "SELECT Users.username, Comments.writing, Comments.id FROM Users, Comments WHERE Comments.review_id=:id AND Comments.user_id = Users.id"
    return db.session.execute(sql, {"id":id}).fetchall()

def find_comment(id):
    sql = "SELECT Users.username, Comments.writing FROM Users, Comments WHERE Comments.id=:id AND Comments.user_id = Users.id"
    return db.session.execute(sql, {"id":id}).fetchone()

def find_comment_edit(id):
    sql = "SELECT Users.username, Comments.writing, Reviews.review, Reviews.id FROM Users, Comments, Reviews WHERE Comments.id=:id AND Comments.review_id = Reviews.id AND Users.id = Comments.user_id"
    return db.session.execute(sql, {"id":id}).fetchone()

def find_comment_path(reply_id):
    sql = "SELECT Reviews.id, Comments.id FROM Reviews, Comments, Replies WHERE Comments.id = Replies.comment_id AND Replies.id=:reply_id AND Comments.review_id = Reviews.id"
    return db.session.execute(sql, {"reply_id":reply_id}).fetchone()

def find_replies(id):
    sql = "SELECT Users.username, Replies.writing, Replies.id FROM Users, Replies WHERE Replies.comment_id=:id AND Replies.user_id = Users.id"
    return db.session.execute(sql, {"id":id}).fetchall()

def find_reply(id):
    sql = "SELECT Users.username, Replies.writing, Comments.writing FROM Users, Replies, Comments WHERE Replies.id=:id AND Replies.comment_id = Comments.id AND Users.id = Replies.user_id"
    return db.session.execute(sql, {"id":id}).fetchone()

def find_report(id,type):
    if type == "work":
        sql = "SELECT * FROM Reports WHERE work_id=:id"
        return db.session.execute(sql, {"id":id}).fetchone()

    if type == "review":
        sql = "SELECT * FROM Reports WHERE review_id=:id"
        return db.session.execute(sql, {"id":id}).fetchone()
    
    if type == "comment":
        sql = "SELECT * FROM Reports WHERE comment_id=:id"
        return db.session.execute(sql, {"id":id}).fetchone()
    
    if type == "reply":
        sql = "SELECT * FROM Reports WHERE reply_id=:id"
        return db.session.execute(sql, {"id":id}).fetchone()

def find_reports():
    return db.session.execute("SELECT * FROM Reports").fetchall()


def insert_user(username,password):
    db.session.execute("INSERT INTO Users (username, moderator, password) VALUES (:username, 0, :password)", {"username":username,"password":password})
    db.session.commit()

def insert_review(name,type,year,language,review,score,user_id):
    sql = "SELECT id FROM Works WHERE LOWER(name)=:name AND type=:type"
    id = db.session.execute(sql, {"name":name.lower(), "type":type}).fetchone()
    if id == None:
        sql = "INSERT INTO Works (name, type, year, language) VALUES (:name,:type,:year,:language) RETURNING id"
        id = db.session.execute(sql, {"name":name,"type":type,"year":year,"language":language}).fetchone()
    work_id = id[0]
    db.session.execute("INSERT INTO Reviews (work_id, user_id, review, score) VALUES (:work_id, :user_id, :review, :score)", {"work_id":work_id,"user_id":user_id,"review":review,"score":score})
    db.session.commit()

def insert_comment(review_id,user_id,writing):
    sql = "INSERT INTO Comments (review_id, user_id, writing) VALUES (:review_id,:user_id,:writing)"
    db.session.execute(sql, {"review_id":review_id,"user_id":user_id,"writing":writing})
    db.session.commit()

def insert_reply(comment_id,user_id,writing):
    sql = "INSERT INTO Replies (comment_id, user_id, writing) VALUES (:comment_id,:user_id,:writing)"
    db.session.execute(sql, {"comment_id":comment_id,"user_id":user_id,"writing":writing})
    db.session.commit()

def insert_work_report(id,reason):
    sql = "INSERT INTO Reports (work_id,report) VALUES (:id,:reason)"
    db.session.execute(sql, {"id":id, "reason":reason})
    db.session.commit()

def insert_review_report(id,reason):
    user_id = find_review_author(id)
    sql = "INSERT INTO Reports (review_id,user_id,report) VALUES (:id,:user_id,:reason)"
    db.session.execute(sql, {"id":id, "user_id":user_id, "reason":reason})
    db.session.commit()

def insert_comment_report(id,reason):
    sql = "SELECT user_id FROM Comments WHERE id=:id"
    user_id = db.session.execute(sql,{"id":id}).fetchone()[0]
    sql = "INSERT INTO Reports (comment_id,user_id,report) VALUES (:id,:user_id,:reason)"
    db.session.execute(sql, {"id":id, "user_id":user_id, "reason":reason})
    db.session.commit()

    review_id = db.session.execute("SELECT review_id from Comments WHERE id=:id", {"id":id}).fetchone()[0]
    return review_id

def insert_reply_report(id,reason):
    sql = "SELECT user_id FROM Replies WHERE id=:id"
    user_id = db.session.execute(sql,{"id":id}).fetchone()[0]
    sql = "INSERT INTO Reports (reply_id,user_id,report) VALUES (:id,:user_id,:reason)"
    db.session.execute(sql, {"id":id, "user_id":user_id, "reason":reason})
    db.session.commit()

    comment_id = db.session.execute("SELECT comment_id from Replies WHERE id=:id", {"id":id}).fetchone()[0]
    review_id = db.session.execute("SELECT review_id from Comments WHERE id=:id", {"id":comment_id}).fetchone()[0]
    return [review_id,comment_id]


def update_work_name(id,name):
    db.session.execute("UPDATE Works SET name=:name WHERE id=:id", {"name":name,"id":id})
    db.session.commit()

def update_work_properties(id,type,year,language):
    db.session.execute("UPDATE Works SET type=:type WHERE id=:id", {"type":type,"id":id})
    db.session.execute("UPDATE Works SET year=:year WHERE id=:id", {"year":year,"id":id})
    db.session.execute("UPDATE Works SET language=:language WHERE id=:id", {"language":language,"id":id})
    db.session.commit()

def update_review(id,review):
    sql = "UPDATE Reviews SET review=:review WHERE id=:id"
    db.session.execute(sql, {"review":review, "id":id})
    db.session.commit()

def update_score(id,score):
    sql = "UPDATE Reviews SET score=:score WHERE id=:id"
    db.session.execute(sql, {"score":score, "id":id})
    db.session.commit()

def update_comment(id,writing):
    db.session.execute("UPDATE Comments SET writing=:writing WHERE id=:id", {"writing":writing,"id":id})
    db.session.commit()

def update_reply(id,writing):
    db.session.execute("UPDATE Replies SET writing=:writing WHERE id=:id", {"writing":writing,"id":id})
    db.session.commit()


def delete_user(user_id):
    sql = "SELECT id from Reviews WHERE user_id=:user_id"
    reviews = db.session.execute(sql, {"user_id":user_id}).fetchall()

    sql = "SELECT id from Comments WHERE user_id=:user_id"
    comments = db.session.execute(sql, {"user_id":user_id}).fetchall()

    sql = "SELECT id from Replies WHERE user_id=:user_id"
    replies = db.session.execute(sql, {"user_id":user_id}).fetchall()

    for review in reviews:
        delete_review(review[0])

    for comment in comments:
        delete_comment(comment[0])

    for reply in replies:
        delete_reply(reply[0])

    db.session.execute("DELETE FROM Users WHERE id=:id", {"id":user_id})
    db.session.commit()

def delete_work(id):
    reviews = db.session.execute("SELECT id from Reviews WHERE work_id=:id", {"id":id}).fetchall()
    for review in reviews:
        db.delete_review(review[0])
    db.session.execute("DELETE FROM Reports WHERE work_id=:id", {"id":id})
    db.session.execute("DELETE FROM Works WHERE id=:id", {"id":id})
    db.session.commit()

def delete_review(id):
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

def delete_comment(id):
    db.session.execute("DELETE FROM Reports WHERE comment_id=:id", {"id":id})
    db.session.execute("DELETE FROM Reports USING Replies WHERE Replies.id = Reports.reply_id AND Replies.comment_id=:id", {"id":id})
    db.session.execute("DELETE FROM Replies WHERE comment_id=:id", {"id":id})
    db.session.execute("DELETE FROM Comments WHERE id=:id", {"id":id})
    db.session.commit()

def delete_reply(id):
    db.session.execute("DELETE FROM Reports WHERE reply_id=:id", {"id":id})
    db.session.execute("DELETE FROM Replies WHERE id=:id", {"id":id})
    db.session.commit()

def delete_report(id,type):
    if type == "work":
        db.session.execute("DELETE FROM Reports WHERE work_id=:id", {"id":id})
    if type == "review":
        db.session.execute("DELETE FROM Reports WHERE review_id=:id", {"id":id})
    if type == "comment":
        db.session.execute("DELETE FROM Reports WHERE comment_id=:id", {"id":id})
    if type == "reply":
        db.session.execute("DELETE FROM Reports WHERE reply_id=:id", {"id":id})
    db.session.commit()
