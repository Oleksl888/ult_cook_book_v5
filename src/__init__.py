"""Notes to future self. It all started here..."""
import os

from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_marshmallow import Marshmallow
import config
from flask_jwt_extended import JWTManager
from flask import Flask


DATA_PATH = os.path.join(config.Config.basedir, 'data')
STATIC_PATH = os.path.join(config.Config.basedir, 'static')

app = Flask(__name__, static_folder=STATIC_PATH)
app.config.from_object(config.Config)
db = SQLAlchemy(app)
ma = Marshmallow(app)
mail = Mail(app)
jwt = JWTManager(app)

from src import routes, schemas, models
from src.database_helpers import initialize_db


initialize_db()
