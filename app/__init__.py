from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
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

    # Register blueprints here
    # Example: Registering a main blueprint
    from app.main import bp as main_bp # Import the main blueprint
    app.register_blueprint(main_bp)

    # Example: Registering an auth blueprint
    from app.auth import bp as auth_bp # Import the auth blueprint
    app.register_blueprint(auth_bp, url_prefix='/auth') # Add /auth prefix to auth routes

    # Register the contest blueprint
    from app.contest import bp as contest_bp
    app.register_blueprint(contest_bp, url_prefix='/contest')

    # Register the admin blueprint
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp)
    # No url_prefix here as it's defined in the blueprint itself

    # Need to import models here *after* db is initialized and *within* the app context
    # or when blueprints that use them are registered.
    # For db.create_all(), it needs to be within the app context.
    with app.app_context():
        from . import models # Import models to register them
        # Consider using Flask-Migrate for database migrations instead of create_all in production
        # Remove or comment out db.create_all() when using Flask-Migrate
        # db.create_all()

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