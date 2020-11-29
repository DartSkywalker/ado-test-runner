from . import db
from flask_login import UserMixin

class user(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    token = db.Column(db.String(100))
    role = db.Column(db.String(100))
    team = db.Column(db.Integer)