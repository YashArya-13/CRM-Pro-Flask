from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth_login"

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    from datetime import datetime

    @app.context_processor
    def inject_now():
        return {'current_year': datetime.now().year}


    app.config.from_object(Config)
    app.url_map.strict_slashes = False
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        # import modules
        from . import routes, models
        db.create_all()

    return app
