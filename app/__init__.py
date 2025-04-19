from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from config import Config
from sqlalchemy import MetaData

# Define naming convention for SQLAlchemy constraints
# See: https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/config/#using-custom-metadata-and-naming-conventions
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Initialize extensions with metadata including the convention
metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
bootstrap = Bootstrap()
login_manager.login_view = 'auth.login' # Blueprint name ('auth') + function name ('login')
login_manager.login_message = u"Por favor, inicia sesión para acceder a esta página."
login_manager.login_message_category = "info"

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions here
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    bootstrap.init_app(app)

    # Register blueprints here
    # Example: Registering a main blueprint
    from app.main import bp as main_blueprint # Import the main blueprint
    app.register_blueprint(main_blueprint)

    # Example: Registering an auth blueprint
    from app.auth import bp as auth_blueprint # Import the auth blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth') # Add /auth prefix to auth routes

    # Register the contest blueprint
    from app.contest import bp as contest_blueprint
    app.register_blueprint(contest_blueprint, url_prefix='/contest')

    # Register the admin blueprint
    from app.admin import bp as admin_blueprint
    app.register_blueprint(admin_blueprint)
    # No url_prefix here as it's defined in the blueprint itself

    with app.app_context():
        from . import models # Import models to register them
        # Create tables if they don't exist (useful for development after db deletion)
        # NOTE: For production, rely on Flask-Migrate ('flask db upgrade')
        # This line should ideally be removed or conditional in production.
        db.create_all()

    # Simple test route (will be replaced by blueprints)
    # @app.route('/test')
    # def test_page():
    #     return '<h1>App Factory Test</h1>'

    # Add context processor to make datetime available in templates
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.utcnow}

    return app 