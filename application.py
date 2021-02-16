import os
import requests

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return "Now"


@app.route("/login",methods=["GET","POST"])
def login():
    notice=""
    if request.method=="POST":
        username=request.form.get('username')
        password=request.form.get('password')
        userlog=request.form.get('userlog')
        passwordlog=request.form.get('passwordlog')
        if userlog==None:                                  ## registration
            data=db.execute("SELECT username FROM users").fetchall()
            for i in range(len(data)):
                if data[i]["username"]==username:
                    notice="Username has been registered"
                    return render_template('login.html',notice=notice)
            db.execute("INSERT INTO users (username,password) VALUES (:username,:password)",{"username":username,"passwod":password})
            db.commit()
            notice="Success!."
        else:                                                 ## registration
            data=db.execute("SELECT * FROM users WHERE username = :userlog",{"userlog":userlog}).fetchone()
            if data!=None:
                if data.username==userlog and data.password==passwordlog:
                    session["username"]=userlog
                    return redirect(url_for("index"))
                else:
                    notice="Wrong input."
            else:
                notice="Wrong input."
    return render_template('login.html',notice=notice)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/api/<string:isbn>")
def api(isbn):
    data=db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn":isbn}).fetchone()
    if data == None:
        return jsonify({"error": "Invalid isbn"}),404
    res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q":isbn})
    data_res=res.json()
    tit= data_res["items"][0]["volumeInfo"]["title"]
    auth=data_res["items"][0]["volumeInfo"]["authors"]
    publisheddate=data_res["items"][0]["volumeInfo"]["publishedDate"]
    isbn_10 = data_res["items"][0]["volumeInfo"]["industryIdentifiers"][0]["identifier"]
    isbn_13 = data_res["items"][0]["volumeInfo"]["industryIdentifiers"][1]["identifier"]
    average_rating=data_res["items"][0]["volumeInfo"]["averageRating"]
    rating_count=data_res["items"][0]["volumeInfo"]["ratingsCount"]
    info_set = {
    "title": tit,
    "author": auth,
    "PublishedDate": publisheddate,
    "isbn_10": isbn_10,
    "isbn_13":isbn_13,
    "averageRating":average_rating,
    "review_count": rating_count,
    }
    return jsonify(info_set)
