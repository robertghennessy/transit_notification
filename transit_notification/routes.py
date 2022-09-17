from flask import Blueprint, render_template, request, redirect, url_for, flash, render_template_string
from transit_notification import db
from transit_notification.models import Operators, Lines
from transit_notification.db import commit_operators, commit_lines, commit_stops, commit_vehicle_monitoring, \
    get_dropdown_values, write_configuration_file

routes = Blueprint('routes', __name__)

@routes.route('/dynamic_dropdown')
def dynamic_dropdown():
    operators_dict = get_dropdown_values()
    return render_template('dynamic_dropdown.html', operators=operators_dict)


@routes.route("/", methods=('GET', 'POST'))
def index():
    error = None
    if request.method == 'POST':
        operator = request.form['operator']
        if not operator:
            error = 'Error occurred: Operator not detected'
        else:
            commit_lines(db, operator)
            commit_stops(db, operator)
            commit_vehicle_monitoring(db, operator)
            return redirect(url_for('routes.index'))

    operators = Operators.query.filter_by(monitored=True).all()
    return render_template("index.html", operators=operators)


@routes.route('/setup/', methods=('GET', 'POST'))
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
            config_dict = {"SIRI": {"api_key": api_key, "base_url": siri_base_url}}
            write_configuration_file(config_dict)
            commit_operators(db, transit_api_key=api_key, siri_base_url=siri_base_url)
            return redirect(url_for('routes.index'))

    return render_template('setup.html', error=error)


@routes.route('/show_operators/')
def show_all_operators():
    return render_template('show_operators.html', operators=Operators.query.all())

@routes.route('/test')
def hello():
    return ('test - routes')



