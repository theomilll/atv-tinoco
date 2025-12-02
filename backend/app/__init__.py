"""Flask application factory."""
import os

from flasgger import Swagger
from flask import Flask

from .config import config
from .extensions import cors, csrf, db, flask_admin, login_manager, migrate


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
    if not app.config.get('TESTING'):
        flask_admin.init_app(app)

    # CORS configuration
    cors.init_app(
        app,
        origins=app.config['CORS_ORIGINS'],
        supports_credentials=app.config['CORS_SUPPORTS_CREDENTIALS'],
        expose_headers=['Content-Type', 'X-CSRFToken'],
        allow_headers=['Content-Type', 'X-CSRFToken', 'Authorization'],
    )

    # Swagger/OpenAPI docs
    Swagger(app, template={
        'info': {
            'title': 'ChatGepeto API',
            'description': 'API do assistente educacional inteligente',
            'version': '1.0.0',
        },
        'securityDefinitions': {
            'cookieAuth': {
                'type': 'apiKey',
                'in': 'cookie',
                'name': 'session'
            }
        }
    })

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

    # Setup Flask-Admin (skip in testing to avoid blueprint collision)
    if not app.config.get('TESTING'):
        from .admin import setup_admin
        setup_admin(flask_admin, db)

    # User loader for Flask-Login
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    return app
