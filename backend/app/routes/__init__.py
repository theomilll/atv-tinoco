"""Flask blueprints registration."""
from flask import Flask


def register_blueprints(app: Flask):
    """Register all blueprints."""
    from .health import bp as health_bp
    from .auth import bp as auth_bp
    from .documents import bp as documents_bp
    from .conversations import bp as conversations_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(conversations_bp)
