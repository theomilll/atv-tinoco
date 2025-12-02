"""Flask configuration classes."""
import os
from pathlib import Path


class Config:
    """Base configuration."""
    BASE_DIR = Path(__file__).resolve().parent.parent

    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session
    SESSION_COOKIE_NAME = 'session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = None  # Allow cross-origin for dev (frontend:3000, api:8000)

    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = False  # We'll check manually for API

    # CORS
    CORS_ORIGINS = os.environ.get(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:3000,http://127.0.0.1:3000'
    ).split(',')
    CORS_SUPPORTS_CREDENTIALS = True

    # File uploads
    UPLOAD_FOLDER = BASE_DIR / 'media'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

    # Celery
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    USE_CELERY = os.environ.get('USE_CELERY', 'False') == 'True'

    # Pagination
    PAGE_SIZE = 20


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{Config.BASE_DIR / 'db.sqlite3'}"
    )
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SESSION_COOKIE_SECURE = False  # ALB is HTTP-only

    # Sentry
    SENTRY_DSN = os.environ.get('SENTRY_DSN')


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
