import os
import sqlite3
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import login_required
import requests

app = Flask(__name__)

## Check for environment variable
#if not os.getenv("DATABASE_URL"):
#    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Choose local or aws database
localDB = False
awsDB = True

#   TODO: the following
#   - check what's inside the aws db (which tables)
#   - create missing tables
#   - make sure the app works with aws db as well

# Set up database
if (localDB == True):
    conn = sqlite3.connect("localDBusers2.db", check_same_thread=False)
    db = conn.cursor()
elif (awsDB==True):
    engine = create_engine("postgres://olrvtxrbdmymxq:2918611898cb3d3600c9a0e21f6c271d3728edfdc6a576e57a90c22affc84cc7@ec2-50-17-178-87.compute-1.amazonaws.com:5432/d6oo9lqp6d2j16")
    db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
@login_required
def index():
#    return render_template("apology.html")
#    db.execute("INSERT INTO firsttest (firstcol, names) VALUES ('132', 'Galymzhan')")
#    db.commit()
#    flights = db.execute("SELECT * FROM firsttest").fetchall()
#    print(flights)
#    sessID = str(session.get("user_id"))
#    return f"Your session ID is {sessID}"
#    return f"<h4> your user id is {sessID} </h4>"
    return render_template("index.html")    

@app.route("/searching", methods = ["POST"])
@login_required
def search():
    isbn = request.form.get("isbn")
    title = request.form.get("title")
    author = request.form.get("author")
#    isbnRes = db.execute("SELECT * FROM books WHERE isbn LIKE '%:isbn%'", {"isbn": isbn})
    Query1 = f"SELECT * FROM books WHERE isbn LIKE '%{isbn}%'"
    Query2 = f"SELECT * FROM books WHERE BookTitle LIKE '%{title}%'"
    Query3 = f"SELECT * FROM books WHERE author LIKE '%{author}%'"
    isbnRes = db.execute(Query1).fetchall()
    titleRes = db.execute(Query2).fetchall()
    authorRes = db.execute(Query3).fetchall()
    tableKeys = ['isbn', 'booktitle', 'author', 'publishyear']
    allRes = []
    allResSet = set()
    for i in range(len(authorRes)):
        allRes.append(tuple(authorRes[i]))
    for i in range(len(isbnRes)):
        allRes.append(tuple(isbnRes[i]))
    for i in range(len(titleRes)):
        allRes.append(tuple(titleRes[i]))
    allResSet = set(allRes)

#             for index in range(len(tableKeys)):
#            print(authorRes[i][tableKeys[index]])
#    for row in authorRes:
#        allResSet.add(row)
#        print(allResSet)
#    for i in range(len(isbnRes)):
#        allRes.append(list(isbnRes[i]))
#    for i in range(len(titleRes)):
#        allRes.append(list(titleRes[i]))
#    for i in range(len(authorRes)):
#        allRes.append(list(authorRes[i]))
#    for i in range(len(allRes)):
#        allRes2.append(allRes[i])
#    print(allRes2)
#    print(allRes)
#    print(allRes)
#    allResSet = set(allRes)
    if(awsDB==True):
        db.close()
        print("connection is closed")

#    return f"AUTHOR: {authorRes} <br> TITLE: {titleRes} <br> ISBN: {isbnRes} <br> ---ALL {allResSet} "    
    return render_template("searchResults.html", allResSet=allResSet)

@app.route("/bookpage/<isbn>", methods=["GET", "POST"])
def bookhome(isbn):
#   TODO: Create a table within your db which stores comments for each book such that:
#    - there is a way to connect the book's comment with the general info about book (foreign key?)
#    - user cannot submit two reviews/scores for the same book
    
#    Make a JOIN request for the book info (general info + reviews)
#   Query your own database for all information about the selected book
    Query1 = f"SELECT * FROM books WHERE isbn='{isbn}'"
    isbnRes = db.execute(Query1).fetchall()

#    Query www.GoodReads.com for their data
#    goodReads = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "2aMU57awaj0ro5no3LOIA", "isbns": isbn})
#    goodReadsData = goodReads.json()
#    return f"great {goodReadsData} <div> {isbnRes}  </div>!!"
    title = isbnRes[0]["booktitle"]
    author = isbnRes[0]["author"]
    published = isbnRes[0]["publishyear"]
#    Get the reviews from the db
    reviews = db.execute("SELECT * FROM reviews WHERE isbn=:a", {"a": isbn}).fetchall()
#    Need to make a class for a review, then store all comments in a list of objects
    score = []
    comment = []
    username = []
    datetime = []
    for j in range(len(reviews)):
        score.append(reviews[j]["score"])
        comment.append(reviews[j]["comment"])
        username.append(reviews[j]["username"])
        datetime.append(reviews[j]["datetime"])
#    print(reviews[1].items())    
    if(awsDB==True):
        db.close()
        print("connection is closed")
    
    return render_template("bookpage.html", isbn=isbn, title=title, author=author,
                           published=published, score=score, comment=comment,
                           username=username, datetime=datetime)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":    
        return render_template("registration.html")
    else:
        if((not request.form.get("username")) or (not request.form.get("password"))):
            return "need to provide username and password"
        if(request.form.get("password") != request.form.get("confirmation")):
            return "passwords do not match"
        username = request.form.get("username")
        password = request.form.get("password")
#       check username for existence in the database
        usernames = db.execute("SELECT username FROM users").fetchall()
        usersList = []
        for i in range(len(usernames)):
            usersList.append(usernames[i][0])
        if str(username) in usersList:
            if(awsDB==True):
                db.close()
            return "such username already exists"
#        insert registration info into db
        db.execute("INSERT INTO users (username, password) VALUES(:user, :pass)", {"user": username, "pass": password})
        if(awsDB==True):
            db.commit()
        elif(localDB==True):
            conn.commit()
        check = db.execute("SELECT* FROM users").fetchall()
        if(awsDB==True):
            db.close()
            print("connection is closed")
        return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    if request.method == "GET":    
        return render_template("login.html")
    else:
        if((not request.form.get("username")) or (not request.form.get("password"))):
            return "need to provide username and password"
        username = request.form.get("username")
        password = request.form.get("password")
#       check for user name existence in the db
        passCheck = db.execute("SELECT password FROM users WHERE username=:user", {"user": username}).fetchall()
        if(len(passCheck)==0):
            if(awsDB==True):
                db.close()
                print("connection is closed")
            return "no such username exists or password is wrong"
##       Check the password
        if(password==passCheck[0][0]):
            if(awsDB==True):
                db.close()
                print("connection is closed")
            session["user_id"] = username
#            return f"success: {password} is the same as {passCheck[0][0]}"
            return redirect("/")
        else:
            if(awsDB==True):
                db.close()
                print("connection is closed")
            return "wrong password"

@app.route("/logout", methods=["GET", "POST"])
def logout():
    # Forget any user_id
    session.clear()

    # Redirect user to login form
#    return redirect("/")
    return redirect("/login")

if __name__ == '__main__':
    app.run()
