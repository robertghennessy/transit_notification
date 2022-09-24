"""Top-level package for Transit notification."""

__author__ = """Robert G Hennessy"""
__email__ = 'robertghennessy@gmail.com'
__version__ = '0.1.0'

from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(test_config=None) -> Flask:
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'ZlfMlXwgvW5ZaomcnVRWYn1E'

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

    db.init_app(app)

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
