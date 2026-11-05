from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from database import db


class User(db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)

    # 1-zu-Many Beziehung zu Filmen (inkl. automatischem Löschen der Filme bei Nutzer-Löschung)
    movies: Mapped[list["Movie"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User {self.name}>"


class Movie(db.Model):
    __tablename__ = 'movies'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(nullable=False)
    year: Mapped[str | None] = mapped_column(nullable=True)
    director: Mapped[str | None] = mapped_column(nullable=True)
    genre: Mapped[str | None] = mapped_column(nullable=True)
    poster_url: Mapped[str | None] = mapped_column(nullable=True)

    # Fremdschlüssel zur User-Tabelle
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Rückwärtsverknüpfung
    user: Mapped["User"] = relationship(back_populates="movies")

    def __repr__(self) -> str:
        return f"<Movie {self.title}>"