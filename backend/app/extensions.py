"""Flask extensions initialization."""
from flask_admin import Admin
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cors = CORS()
csrf = CSRFProtect()
flask_admin = Admin(name='ChatGepeto Admin', template_mode='bootstrap4')
