import os

from flask import Flask, abort, flash, render_template, request, redirect, url_for
import requests
from sqlalchemy import inspect, text
from database import db
from models import User, Movie

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")

# Konfiguration der SQLite-Datenbank
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///moviweb.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Datenbank mit Flask verknüpfen
db.init_app(app)

OMDB_API_KEY = "6083869b"  # Hier deinen OMDb API-Key eintragen

# Tabellen beim Start automatisch erstellen
with app.app_context():
    db.create_all()
    movie_columns = {column["name"] for column in inspect(db.engine).get_columns("movies")}
    if "poster_url" not in movie_columns:
        db.session.execute(text("ALTER TABLE movies ADD COLUMN poster_url VARCHAR"))
        db.session.commit()


@app.route("/")
def index():
    """Startseite: Alle Nutzer abrufen und anzeigen (im modernen 2.0 Select-Stil)."""
    statement = db.select(User)
    users = db.session.execute(statement).scalars().all()
    return render_template("index.html", users=users)


@app.route("/add_user", methods=["POST"])
def add_user():
    """Neuen Nutzer anlegen."""
    name = request.form.get("name", "").strip()
    if not name:
        flash("Bitte gib einen Namen ein.", "error")
        return redirect(url_for("index"))

    statement = db.select(User).filter_by(name=name)
    existing_user = db.session.execute(statement).scalar_one_or_none()
    if existing_user:
        flash("Dieser Nutzername ist bereits vergeben.", "error")
    else:
        db.session.add(User(name=name))
        db.session.commit()
        flash(f"Nutzer „{name}“ wurde angelegt.", "success")
    return redirect(url_for("index"))


@app.route("/user/<int:user_id>")
def user_movies(user_id):
    """Filmbibliothek des Nutzers anzeigen."""
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    movies = user.movies
    return render_template("movies.html", user=user, movies=movies)


@app.route("/user/<int:user_id>/add", methods=["POST"])
def add_movie(user_id):
    """Film über OMDb API suchen und speichern."""
    movie_title = request.form.get("title", "").strip()
    if not movie_title:
        flash("Bitte gib einen Filmtitel ein.", "error")
        return redirect(url_for("user_movies", user_id=user_id))

    if not db.session.get(User, user_id):
        abort(404)

    try:
        response = requests.get(
            "https://www.omdbapi.com/",
            params={"t": movie_title, "apikey": OMDB_API_KEY},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        flash("OMDb ist gerade nicht erreichbar. Bitte versuche es später erneut.", "error")
        return redirect(url_for("user_movies", user_id=user_id))

    if data.get("Response") != "True":
        if data.get("Error") == "Movie not found!":
            flash(f"Zu „{movie_title}“ wurde kein Film gefunden.", "error")
        else:
            flash("OMDb konnte den Film nicht suchen. Bitte prüfe die API-Konfiguration.", "error")
        return redirect(url_for("user_movies", user_id=user_id))

    poster_url = data.get("Poster")
    if poster_url == "N/A":
        poster_url = None
    new_movie = Movie(
        title=data.get("Title") or movie_title,
        year=data.get("Year"),
        director=data.get("Director"),
        genre=data.get("Genre"),
        poster_url=poster_url,
        user_id=user_id
    )
    db.session.add(new_movie)
    db.session.commit()
    flash(f"„{new_movie.title}“ wurde hinzugefügt.", "success")
    return redirect(url_for("user_movies", user_id=user_id))


@app.route("/movie/delete/<int:movie_id>/<int:user_id>")
def delete_movie(movie_id, user_id):
    """Film löschen."""
    movie = db.session.get(Movie, movie_id)
    if not movie or movie.user_id != user_id:
        abort(404)
    db.session.delete(movie)
    db.session.commit()
    flash("Film wurde gelöscht.", "success")
    return redirect(url_for("user_movies", user_id=user_id))


@app.route("/movie/update/<int:movie_id>/<int:user_id>", methods=["POST"])
def update_movie(movie_id, user_id):
    """Filmdaten aktualisieren."""
    movie = db.session.get(Movie, movie_id)
    if not movie or movie.user_id != user_id:
        abort(404)
    movie.title = request.form.get("title")
    movie.year = request.form.get("year")
    movie.director = request.form.get("director")
    movie.genre = request.form.get("genre")
    db.session.commit()
    flash("Filmdaten wurden gespeichert.", "success")
    return redirect(url_for("user_movies", user_id=user_id))


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)