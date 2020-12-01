from flask import Flask, g, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user


# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'secret-key-goes-here'
    postgres = 'postgresql+psycopg2://user:user@localhost:5432/maindb'

    app.config['SQLALCHEMY_DATABASE_URI'] = postgres

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import user

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return user.query.get(int(user_id))

    with app.app_context():
        # blueprint for auth routes in our app
        from .auth import auth as auth_blueprint
        app.register_blueprint(auth_blueprint)

        # blueprint for non-auth parts of app
        from .main import main as main_blueprint
        app.register_blueprint(main_blueprint)

    return app

# def create_app(app_config):
#     app = Flask(__name__)
#     with app.app_context():
#         from your_app.somewhere import team_name
#
#         app.register_blueprint(team_name)
#     return app