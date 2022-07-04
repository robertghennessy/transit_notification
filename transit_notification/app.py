from flask import Flask
import os
from flask import Flask, render_template, request, redirect, url_for, flash, render_template_string
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


def get_dropdown_values():
    """
    dummy function, replace with e.g. database call. If data not change, this function is not needed but dictionary
could be defined globally
    """

    # Create a dictionary (myDict) where the key is
    # the name of the brand, and the list includes the names of the car models
    #
    # Read from the database the list of cars and the list of models.
    # With this information, build a dictionary that includes the list of models by brand.
    # This dictionary is used to feed the drop down boxes of car brands and car models that belong to a car brand.
    #
    # Example:
    #
    # {'Toyota': ['Tercel', 'Prius'],
    #  'Honda': ['Accord', 'Brio']}

    operators = Operators.query.all()
    # Create an empty dictionary
    operator_dict = {}
    for operator in operators:

        name = operator.name
        operator_id = operator.id

        """
        # Select all car models that belong to a car brand
        q = Carmodels.query.filter_by(brand_id=brand_id).all()

        # build the structure (lst_c) that includes the names of the car models that belong to the car brand
        lst_c = []
        for c in q:
            lst_c.append(c.car_model)
        """
        operator_dict[name] = operator_id #lst_c

    return operator_dict

class Operators(db.Model):
    id = db.Column(db.String(2), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    monitored = db.Column(db.Boolean, nullable=False)
    lines_date = db.Column(db.DateTime)
    lines = db.relationship('Lines', backref='operator', lazy=True)

    def __repr__(self):
        return f"Id : {self.id}, Name: {self.name}, Monitored: {self.monitored}, Lines Date: {self.lines_date}"


class Lines(db.Model):
    id = db.Column(db.String(2), primary_key=True)
    operator_id = db.Column(db.String(2), db.ForeignKey("operators.id"), nullable=False)
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

@app.route('/')
def index():
    operators_dict = get_dropdown_values()
    return render_template('index.html', operators=operators_dict)


@app.route("/input", methods=('GET', 'POST'))
def input():
    error = None
    if request.method == 'POST':
        operator = request.form['operator']

        if not operator:
            error = 'Error occurred: Operator not detected'
        else:
            return redirect(url_for('index'))

    operators = Operators.query.filter_by(monitored=True).all()
    return render_template("input.html", operators=operators)


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
            init_db()
            commit_operators(db, transit_api_key=api_key, siri_base_url=siri_base_url)
            return redirect(url_for('index'))

    return render_template('setup.html', error=error)


@app.route('/show_operators/')
def show_all_operators():
    return render_template('show_operators.html', operators=Operators.query.all())


