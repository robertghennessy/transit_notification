from flask import Blueprint, render_template, request, redirect, url_for, flash, render_template_string
from transit_notification import db
from transit_notification.models import Operators, Lines
from transit_notification.db_commands import commit_operators, commit_lines, commit_stops, commit_vehicle_monitoring, \
    get_dropdown_values, write_configuration_file, commit_pattern
import siri_transit_api_client

routes = Blueprint('routes', __name__)


@routes.route('/dynamic_dropdown')
def dynamic_dropdown():
    operators_dict = get_dropdown_values()
    return render_template('dynamic_dropdown.html', operators=operators_dict)


@routes.route("/dropdown", methods=('GET', 'POST'))
def dropdown():
    error = None
    if request.method == 'POST':
        operator = request.form['operator']
        if not operator:
            error = 'Error occurred: Operator not detected'
        else:
            commit_lines(db, operator)
            commit_stops(db, operator)
            commit_vehicle_monitoring(db, operator)
            return render_template('show_lines.html', lines=Lines.query.order_by(Lines.sort_index.asc()).all())

    operators = Operators.query.filter_by(monitored=True).all()
    return render_template("dropdown.html", operators=operators)


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
            try:
                commit_operators(db, transit_api_key=api_key, siri_base_url=siri_base_url)
            except siri_transit_api_client.exceptions.TransportError:
                error = 'Unable to establish connection to {0}. Please check url and resubmit.'.format(siri_base_url)
                return render_template('setup.html', error=error)
            except siri_transit_api_client.exceptions.ApiError:
                error = 'This API key provided is invalid.'
                return render_template('setup.html', error=error)
            return redirect(url_for('routes.index'))
    return render_template('setup.html', error=error)


@routes.route('/')
def index():
    operator_val = db.session.query(Operators).first()
    if operator_val is None:
        error = 'Need to provide api address and api key before using'
        return redirect(url_for('routes.setup'))
    return render_template('index.html',
                           operators=Operators.query.filter(Operators.monitored == True).all())


@routes.route('/test')
def test():
    return 'test - routes'


@routes.route('/operator/<operator_id>', methods=["GET"])
def render_lines(operator_id):
    operator_val = Operators.query.filter(Operators.id == operator_id).first()
    if operator_val is None:
        error = 'Operator {0} is not supported.'.format(operator_id)
        return render_template('index.html',
                               operators=Operators.query.filter(Operators.monitored == True).all(),
                               error=error)
    commit_lines(db, operator_id)
    commit_stops(db, operator_id)
    commit_vehicle_monitoring(db, operator_id)
    return render_template('show_lines.html',
                           lines=Lines.query.filter(Lines.operator_id == operator_id).order_by(Lines.sort_index.asc()))


@routes.route('/operator/<operator_id>/<line_id>', methods=["GET"])
def render_stops(operator_id, line_id):
    operator_val = Operators.query.filter(Operators.id == operator_id).first()
    line_val = Lines.query.filter(db.and_(Lines.operator_id == operator_id, Lines.id == line_id)).first()
    if operator_val is None:
        error = 'Operator {0} is not supported.'.format(operator_id)
        return render_template('index.html',
                               operators=Operators.query.filter(Operators.monitored == True).all(),
                               error=error)
    if line_val is None:
        error = 'Operator {0} with line {1} is not supported.'.format(operator_id, line_id)
        return render_template('show_lines.html',
                               lines=Lines.query.filter(Lines.operator_id == operator_id).order_by(Lines.sort_index.asc()))
    commit_pattern(db, operator_id, line_id)
    return render_template('show_lines.html',
                           lines=Lines.query.filter(Lines.operator_id == operator_id).order_by(Lines.sort_index.asc()))
