import datetime
import uuid
from dataclasses import asdict
from flask import Blueprint, render_template, session, request, redirect, current_app, url_for, flash
from passlib.handlers.pbkdf2 import pbkdf2_sha256

from forms import MovieForm, EditedForm, RegisterForm,LoginForm,DescriptionForm
from module import Movie, User
import functools
pages = Blueprint(
    "pages", __name__, template_folder="templates", static_folder="static"
)

def login_required(route):
    @functools.wraps(route)
    def route_wrapper(*args, **kwargs):
        if session.get("email") is None:
            return redirect(url_for(".login"))

        return route(*args, **kwargs)

    return route_wrapper

@pages.route("/movie/<string:_id>/description",methods=["GET","POST"])
@login_required
def description(_id):
    form=DescriptionForm()
    if form.validate_on_submit():
        current_app.db.entries.update_one({"_id": _id}, {"$set": {"description": form.description.data}})
        return redirect(url_for(".view",_id=_id))
    return render_template("description.html",form=form)

@pages.get("/logout")
@login_required
def logout():
    del session["email"]
    return redirect(url_for(".login"))

@pages.route("/login",methods=["GET","POST"])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user_data=current_app.db.user.find_one({"email":form.email.data})
        if(not user_data):
           flash("Login unsucessful",category="danger")
           return redirect(url_for(".login"))
        user=User(**user_data)
        if pbkdf2_sha256.verify(form.password.data, user.password):
            session["email"]=user.email
            session["user_id"]=user._id
            return redirect(url_for(".index"))

    return render_template("login.html",form=form)

@pages.route("/register",methods=["GET","POST"])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        user = User(
            _id=uuid.uuid4().hex,
            email=form.email.data,
            password=pbkdf2_sha256.hash(form.password.data),
        )
        current_app.db.user.insert_one(asdict(user))
        return redirect(url_for(".login"))

    return render_template("register.html",form=form)

@pages.route("/")
@login_required
def index():
    user_data = current_app.db.user.find_one({"email": session["email"]})
    user = User(**user_data)
    movie_data = current_app.db.entries.find({"_id": {"$in": user.movies}})
    movies=[Movie(**movie) for movie in movie_data]

    return render_template("index.html",title="Movies Watchlist",movies_data=movies)


@pages.route("/add", methods=["GET","POST"])
@login_required
def add_movie():
    form=MovieForm()
    if form.validate_on_submit():
        movie = Movie(
            _id=uuid.uuid4().hex,
            title=form.title.data,
            director=form.director.data,
            year=form.year.data
        )
        current_app.db.entries.insert_one(asdict(movie))
        current_app.db.user.update_one({"_id": session["user_id"]}, {"$push": {"movies": movie._id}})
        return redirect(url_for(".index"))
    return render_template("new_movie.html",title="Movies Watchlist - Add Movie", form=form)

@pages.get("/toggle-theme")
def toggle_theme():
    current_theme = session.get("theme")
    if current_theme == "dark":
        session["theme"] = "light"
    else:
        session["theme"] = "dark"

    return redirect(request.args.get("current_page"))

@pages.get("/movie/<string:_id>/view")
def view(_id:str):
    movie=Movie(**current_app.db.entries.find_one({"_id":_id}))

    return render_template("movies_detail.html",movie=movie)

@pages.get("/movie/<string:_id>/rate")
@login_required
def rate(_id:str):
    rating = int(request.args.get("rating"))
    current_app.db.entries.update_one({"_id": _id}, {"$set": {"rating": rating}})

    return redirect(url_for(".view",_id=_id))

@pages.get("/movie/<string:_id>/watch")
@login_required
def watch(_id):
    current_app.db.entries.update_one({"_id": _id}, {"$set": {"last_watched": datetime.datetime.today()}})
    return redirect(url_for(".view", _id=_id))

@pages.route("/movie/<string:_id>/edit",methods=["GET","POST"])
@login_required
def edit(_id):
    movie=Movie(**current_app.db.entries.find_one({"_id":_id}))
    form=EditedForm(obj=movie)
    if form.validate_on_submit():
        movie.title = form.title.data
        movie.director = form.director.data
        movie.year = form.year.data
        movie.cast = form.cast.data
        movie.series = form.series.data
        movie.tags = form.tags.data
        movie.description = form.description.data
        movie.video_link = form.video_link.data
        current_app.db.entries.update_one({"_id": movie._id}, {"$set": asdict(movie)})
        return redirect(url_for(".view",_id=movie._id))


    return render_template("edit.html",form=form)
