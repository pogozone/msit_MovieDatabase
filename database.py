from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Moderne Basisklasse für alle SQLAlchemy 2.0 Modelle
class Base(DeclarativeBase):
    pass

# Flask-SQLAlchemy Instanz mit unserer modernen Base verknüpfen
db = SQLAlchemy(model_class=Base)