#!/usr/bin/env python
"""Flask CLI commands."""
import click
from flask.cli import FlaskGroup

from app import create_app
from app.extensions import db
from app.models import User


def create_cli_app():
    return create_app()


@click.group(cls=FlaskGroup, create_app=create_cli_app)
def cli():
    """Management CLI for ChatGepeto (Flask)."""
    pass


@cli.command()
@click.option('--username', default='gepetobot', help='Username')
@click.option('--email', default='gepetobot@chatgepeto.com', help='Email')
@click.option('--password', default='cesariscool', help='Password')
def create_superuser(username, email, password):
    """Create superuser account."""
    existing = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing:
        click.echo(f'User already exists: {existing.username}')
        return

    user = User(
        username=username,
        email=email,
        is_active=True,
        is_staff=True,
        is_superuser=True
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    click.echo(f'Superuser created: {username}')


@cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    click.echo('Database initialized.')


if __name__ == '__main__':
    cli()
