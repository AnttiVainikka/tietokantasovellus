from flask import session
import db

def check_author(author):
    try:
        username = session["username"]
        if username == author:
            return True
    except KeyError:
        pass
    return False

def check_moderator():
    try:
        username = session["username"]
        moderator = db.find_moderator(username)
        if moderator == 1:
            return True
    except KeyError:
        pass
    return False

def name_order(work):
    return work[1].lower()
