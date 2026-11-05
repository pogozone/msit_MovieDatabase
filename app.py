from flask import Flask, render_template, request, redirect, url_for
import requests
from sqlalchemy import inspect, text
from database import db
from models import User, Movie

app = Flask(__name__)

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
    name = request.form.get("name")
    if name:
        # Prüfen, ob der Nutzer schon existiert
        statement = db.select(User).filter_by(name=name)
        existing_user = db.session.execute(statement).scalar_one_or_none()

        if not existing_user:
            new_user = User(name=name)
            db.session.add(new_user)
            db.session.commit()

    return redirect(url_for("index"))


@app.route("/user/<int:user_id>")
def user_movies(user_id):
    """Filmbibliothek des Nutzers anzeigen."""
    user = db.session.get(User, user_id)
    if not user:
        return "Nutzer nicht gefunden", 404

    return render_template("movies.html", user=user, movies=user.movies)


@app.route("/user/<int:user_id>/add", methods=["POST"])
def add_movie(user_id):
    """Film über OMDb API suchen und speichern."""
    movie_title = request.form.get("title")

    if movie_title:
        response = requests.get(
            "https://www.omdbapi.com/",
            params={"t": movie_title, "apikey": OMDB_API_KEY},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("Response") == "True":
            title = data.get("Title")
            year = data.get("Year")
            director = data.get("Director")
            genre = data.get("Genre")
            poster_url = data.get("Poster")
            if poster_url == "N/A":
                poster_url = None
        else:
            title = movie_title
            year = "Unbekannt"
            director = "Unbekannt"
            genre = "Unbekannt"
            poster_url = None

        new_movie = Movie(
            title=title,
            year=year,
            director=director,
            genre=genre,
            poster_url=poster_url,
            user_id=user_id
        )
        db.session.add(new_movie)
        db.session.commit()

    return redirect(url_for("user_movies", user_id=user_id))


@app.route("/movie/delete/<int:movie_id>/<int:user_id>")
def delete_movie(movie_id, user_id):
    """Film löschen."""
    movie = db.session.get(Movie, movie_id)
    if movie:
        db.session.delete(movie)
        db.session.commit()
    return redirect(url_for("user_movies", user_id=user_id))


@app.route("/movie/update/<int:movie_id>/<int:user_id>", methods=["POST"])
def update_movie(movie_id, user_id):
    """Filmdaten aktualisieren."""
    movie = db.session.get(Movie, movie_id)
    if movie:
        movie.title = request.form.get("title")
        movie.year = request.form.get("year")
        movie.director = request.form.get("director")
        movie.genre = request.form.get("genre")
        db.session.commit()

    return redirect(url_for("user_movies", user_id=user_id))


if __name__ == "__main__":
    app.run(debug=True)