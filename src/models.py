import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from werkzeug.security import generate_password_hash

from src import db


class Recipe(db.Model):
    __tablename__ = 'recepies'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    recipe = Column(String)
    ingridients = db.relationship('Ingridient', secondary='recipe_ingridients',
                                  lazy='subquery', backref=db.backref('recepies', lazy=True))

    def __init__(self, name: str, recipe: str, ingridients=None):
        self.name = name
        self.recipe = recipe
        self.ingridients = [] if not ingridients else ingridients

    def __repr__(self):
        return f'Recipe for <{self.name}>, {self.ingridients}'


class Ingridient(db.Model):
    __tablename__ = 'ingridients'
    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f'Ingridient <{self.name}>'


class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    message = Column(String)
    date_time = Column(DateTime)

    def __init__(self, name: str, message: str):
        self.name = name
        self.message = message
        self.date_time = datetime.now()

    def __repr__(self):
        return f'Feedback object'


class Tracker(db.Model):
    __tablename__ = 'iptracker'
    id = Column(Integer, primary_key=True)
    ipaddress = Column(String)
    city = Column(String)
    country = Column(String)
    date_time = Column(DateTime)
    action = Column(String, default='Visit')

    def __init__(self, ipaddress: str, city: str, country: str, action=None):
        self.ipaddress = ipaddress
        self.city = city
        self.country = country
        self.date_time = datetime.now()
        self.action = 'Visit' if not action else action

    # @staticmethod
    # def get_ip_info():
    #     """Connect geo_api functions to call them during object initialization"""
    #     ipaddress = 'Unknown'
    #     city = 'Unknown'
    #     country = 'Unknown'

    def __repr__(self):
        return f'Iptracker <{self.ipaddress}>, <{self.city}>, <{self.country}>'


class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(String)
    uuid = Column(String)
    registered_date = Column(DateTime)
    current_login = Column(DateTime)
    last_login = Column(DateTime)
    userpic = Column(String)
    is_admin = Column(Boolean, default=False)

    def __init__(self, name: str, email: str, password: str):
        self.name = name
        self.email = email
        self.password = generate_password_hash(password)
        self.registered_date = datetime.now()
        self.uuid = str(uuid.uuid4())

    def __repr__(self):
        return f'User <{self.name}>, Email <{self.email}>'


class RecipeFeedback(db.Model):
    __tablename__ = 'recipe_feedback'
    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recepies.id'))
    recipe = db.relationship('Recipe', lazy='subquery', backref=db.backref('recipe_feedback', lazy=True))
    user_id = Column(Integer, ForeignKey('users.id'))
    user = db.relationship('User', lazy='subquery', backref=db.backref('recipe_feedback', lazy=True))
    message = Column(String)
    ip = Column(String)
    date_time = Column(DateTime)

    def __init__(self, recipe_id: int, user_id: int, message: str, ip: str):
        self.recipe_id = recipe_id
        self.user_id = user_id
        self.message = message
        self.ip = ip
        self.date_time = datetime.now()
        self.recipe = db.session.query(Recipe).filter_by(id=recipe_id).first()
        self.user = db.session.query(User).filter_by(id=user_id).first()

    def __repr__(self):
        return f'Recipe Feedback object'


# class RecipeIngridients(db.Model):
#     __tablename__ = 'recipe_ingridients'
#     recipe_id = Column(Integer, ForeignKey('recepies.id'), primary_key=True)
#     recipe = db.relationship('Recipe', lazy='subquery', backref=db.backref('recipe_ingridients', lazy=True))
#     ingridient_id = Column(Integer, ForeignKey('ingridients.id'), primary_key=True)
#     ingridient = db.relationship('Ingridient', lazy='subquery', backref=db.backref('recipe_ingridients', lazy=True))
#
#     def __init__(self, recipe_id: int, ingridient_id: int):
#         self.recipe_id = recipe_id
#         self.ingridient_id = ingridient_id
#         self.recipe = db.session.query(Recipe).filter_by(id=recipe_id).first()
#         self.ingridient = db.session.query(Ingridient).filter_by(id=ingridient_id).first()
#
#     def __repr__(self):
#         return f'Recipe-Ingridients object'

class RecipeIngridients(db.Model):
    __tablename__ = 'recipe_ingridients'
    recipe_id = Column(Integer, ForeignKey('recepies.id'), primary_key=True)
    ingridient_id = Column(Integer, ForeignKey('ingridients.id'), primary_key=True)

    def __init__(self, recipe_id: int, ingridient_id: int):
        self.recipe_id = recipe_id
        self.ingridient_id = ingridient_id

    def __repr__(self):
        return f'Recipe-Ingridients object'
