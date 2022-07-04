from flask import Flask
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import siri_transit_api_client
import pandas as pd
# from transit_notification.db_functions import commit_operators

basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()


def create_app():
    new_app = Flask(__name__)
    new_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
    new_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    new_app.config['SECRET_KEY'] = 'ZlfMlXwgvW5ZaomcnVRWYn1E'
    db.init_app(new_app)
    return new_app


def init_db():
    """
    Initialize the database
    """
    db.drop_all(app=create_app())
    db.create_all(app=create_app())


class Operators(db.Model):
    id = db.Column(db.String(2), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    monitored = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return f"Id : {self.id}, Name: {self.name}, Monitored: {self.monitored}"


def commit_operators(siri_db, transit_api_key, siri_base_url):
    siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
    operators_dict = siri_client.operators()
    operators_df = pd.DataFrame(operators_dict)

    operators = [Operators(id=row['Id'], name=row['Name'], monitored=row['Monitored'])
                 for _, row in operators_df.iterrows()]

    siri_db.session.add_all(operators)
    siri_db.session.commit()
    return None


app = create_app()
app.app_context().push()


messages = [{'title': 'Message One',
             'content': 'Message One Content'},
            {'title': 'Message Two',
             'content': 'Message Two Content'}
            ]


@app.route('/')
def index():
    return render_template('index.html', messages=messages)


@app.route('/setup/', methods=('GET', 'POST'))
def setup():
    error = None
    if request.method == 'POST':
        api_key = request.form['api_key']
        siri_base_url = request.form['siri_base_url']

        if not siri_base_url and not api_key:
            error = 'SIRI Base URL and API key are required!'
        elif not siri_base_url:
            error = 'SIRI Base URL is required!'
        elif not api_key:
            error = 'API Key is required!'
        else:
            messages.append({'title': api_key, 'content': siri_base_url})
            init_db()
            commit_operators(db, transit_api_key=api_key, siri_base_url=siri_base_url)
            return redirect(url_for('index'))

    return render_template('setup.html', error=error)

@app.route('/show_operators/')
def show_all():
   return render_template('show_operators.html', operators=Operators.query.all())
