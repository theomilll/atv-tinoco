"""Flask application factory."""
import os
from flask import Flask

from .config import config
from .extensions import db, migrate, login_manager, cors, csrf, flask_admin


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    flask_admin.init_app(app)

    # CORS configuration
    cors.init_app(
        app,
        origins=app.config['CORS_ORIGINS'],
        supports_credentials=app.config['CORS_SUPPORTS_CREDENTIALS'],
        expose_headers=['Content-Type', 'X-CSRFToken'],
        allow_headers=['Content-Type', 'X-CSRFToken', 'Authorization'],
    )

    # Ensure upload directory exists
    app.config['UPLOAD_FOLDER'].mkdir(parents=True, exist_ok=True)

    # Setup Sentry if configured
    if app.config.get('SENTRY_DSN'):
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.1,
        )

    # Register blueprints
    from .routes import register_blueprints
    register_blueprints(app)

    # Setup Flask-Admin
    from .admin import setup_admin
    setup_admin(flask_admin, db)

    # User loader for Flask-Login
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    return app
