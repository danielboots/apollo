import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_reviews")
def get_reviews():
    reviews = list(mongo.db.reviews.find())
    return render_template("reviews.html", reviews=reviews)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    reviews = list(mongo.db.reviews.find({"$text": {"$search": query}}))
    return render_template("reviews.html", reviews=reviews)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input - Allen Mentor Help
            if check_password_hash(
                existing_user["password"],
                request.form.get("password")
            ):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        reviews = list(mongo.db.reviews.find(
            {"created_by": {"$eq": session["user"]}})
        )
        return render_template(
            "profile.html", username=username, reviews=reviews
        )

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_review", methods=["GET", "POST"])
def add_review():
    if request.method == "POST":
        review = {
            "genre": request.form.get("genre"),
            "artist_name": request.form.get("artist_name"),
            "track_title": request.form.get("track_title"),
            "album_title": request.form.get("album_title"),
            "artwork": request.form.get("artwork"),
            "youtube": request.form.get("youtube"),
            "review": request.form.get("review"),
            "hot_not": request.form.get("hot_not"),
            "created_by": session["user"]
        }
        mongo.db.reviews.insert_one(review)
        flash("Review Successfully Added")
        return redirect(url_for("get_reviews"))

    genre = mongo.db.genre.find().sort("genre", 1)
    return render_template("add_review.html", genre=genre)


@app.route("/edit_review/<review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    if request.method == "POST":
        submit = {
            "genre": request.form.get("genre"),
            "artist_name": request.form.get("artist_name"),
            "track_title": request.form.get("track_title"),
            "album_title": request.form.get("album_title"),
            "artwork": request.form.get("artwork"),
            "youtube": request.form.get("youtube"),
            "review": request.form.get("review"),
            "hot_not": request.form.get("hot_not"),
            "created_by": session["user"]
        }
        mongo.db.reviews.update({"_id": ObjectId(review_id)}, submit)
        flash("Review Successfully updated")

    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})

    genre = mongo.db.genre.find().sort("genre", 1)
    return render_template("edit_review.html", review=review, genre=genre)


@app.route("/delete_review/<review_id>")
def delete_review(review_id):
    mongo.db.reviews.remove({"_id": ObjectId(review_id)})
    flash("Review Successfully Deleted ")
    return redirect(url_for("get_reviews"))


@app.route("/get_genre")
def get_genres():
    genres = list(mongo.db.genre.find().sort("genre", 1))
    return render_template("genres.html", genres=genres)


@app.route("/add_genre", methods=["GET", "POST"])
def add_genre():
    if request.method == "POST":
        genre = {
            "genre": request.form.get("genre")
        }
        mongo.db.genre.insert_one(genre)
        flash("New Genre Added")
        return redirect(url_for("get_genres"))

    return render_template("add_genre.html")


@app.route("/edit_genre/<genre_id>", methods=["GET", "POST"])
def edit_genre(genre_id):
    if request.method == "POST":
        submit = {
            "genre": request.form.get("genre")
        }
        mongo.db.genre.update({"_id": ObjectId(genre_id)}, submit)
        flash("Genre Successfully Updated")
        return redirect(url_for("get_genres"))
    genre = mongo.db.genre.find_one({"_id": ObjectId(genre_id)})
    return render_template("edit_genre.html", genre=genre)


@app.route("/delete_genre/<genre_id>")
def delete_genre(genre_id):
    mongo.db.genre.remove({"_id": ObjectId(genre_id)})
    flash("genre Successfully Deleted")
    return redirect(url_for("get_genres"))


# View review - custom addition to program.
@app.route("/view_review/<review_id>", methods=["GET"])
def view_review(review_id):

    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    return render_template("view_review.html", review=review)


# Addition of 404 page function - From Flask Docs:
# Code from 'https://flask.palletsprojects.com/en/1.1.x/patterns/errorpages/'
@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
