"""Top-level package for Transit notification."""

import click
from flask import Flask
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
import os
import configparser


__author__ = """Robert G Hennessy"""
__email__ = 'robertghennessy@gmail.com'
__version__ = '0.1.0'

db = SQLAlchemy()

def create_app(test_config=None) -> Flask:
    app = Flask(__name__)

    # some deploy systems set the database url in the environ
    db_url = os.environ.get("DATABASE_URL")
    db_url = 'sqlite:////Users/roberthennessy/Documents/python_project/transit_notification/tests/test_database/scratch.db'

    if db_url is None:
        # default to a sqlite database in the instance folder
        db_url = 'sqlite:///' + os.path.join(app.instance_path, 'database.db')

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        SQLALCHEMY_DATABASE_URI=db_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # initialize Flask-SQLAlchemy and the init-db command
    db.init_app(app)
    app.cli.add_command(init_db_command)

    if bool(os.environ.get("RESET_TABLES", "dev")) is True:
        with app.app_context():
            from transit_notification import models
            db.drop_all()
            db.create_all()  # Create sql tables for our data models

    from transit_notification import views, routes
    app.register_blueprint(views.bp)
    app.register_blueprint(routes.routes)

    @app.route('/hello')
    def hello():
        return 'Hello World!'

    return app


def init_db():
    db.drop_all()
    db.create_all()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")
