from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from decouple import config
import os

db = SQLAlchemy()

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app/static/images')

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = config('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = config('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config('SQLALCHEMY_TRACK_MODIFICATIONS', default=False)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    db.init_app(app)
    Migrate(app, db)

    from . import models
    from .routes import register_routes
    
    register_routes(app)

    return app
