from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_mail import Mail
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()  
api = Api()
mail = Mail()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()