from flask import Blueprint, render_template, request, redirect, url_for, flash
from transit_notification import db
from transit_notification.models import Operators, Lines, Patterns, StopPatterns, Stops
import siri_transit_api_client
import datetime as dt
import transit_notification.db_commands as tndc

routes = Blueprint('routes', __name__)

# units are hours
OPERATORS_REFRESH_LIMIT = 24
LINES_REFRESH_LIMIT = 24
STOPS_REFRESH_LIMIT = 24
PATTERN_REFRESH_LIMIT = 24
VEHICLE_MONITORING_REFRESH_LIMIT = 24


@routes.route('/setup', methods=('GET', 'POST'))
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
            tndc.write_key_api_file(config_dict)
            try:
                operators_json = tndc.get_operators_dict(transit_api_key=api_key, siri_base_url=siri_base_url)
                tndc.save_operators(db, operators_json)
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
        flash(error, 'error')
        return redirect(url_for('routes.setup'))
    return render_template('index.html',
                           operators=Operators.query.filter(Operators.operator_monitored).all())


@routes.route('/operator/<operator_id>', methods=["GET"])
def render_lines(operator_id):
    operator_check = check_valid_operator(operator_id)
    if operator_check is not None:
        return operator_check
    current_time = dt.datetime.now(dt.timezone.utc)
    transit_api_key, siri_base_url = tndc.read_key_api_file()
    if tndc.refresh_needed(db, operator_id, 'lines_updated', LINES_REFRESH_LIMIT):
        lines_dict = tndc.get_lines_dict(transit_api_key, siri_base_url, operator_id)
        tndc.save_lines(db, operator_id, lines_dict, current_time)
    if tndc.refresh_needed(db, operator_id, 'stops_updated', STOPS_REFRESH_LIMIT):
        stops_dict = tndc.get_stops_dict(transit_api_key, siri_base_url, operator_id)
        tndc.save_stops(db, operator_id, stops_dict, current_time)
    if tndc.refresh_needed(db, operator_id, 'vehicle_monitoring_updated', VEHICLE_MONITORING_REFRESH_LIMIT):
        vehicle_monitoring_dict = tndc.get_vehicle_monitoring_dict(transit_api_key, siri_base_url, operator_id)
        tndc.save_vehicle_monitoring(db, operator_id, vehicle_monitoring_dict, current_time)
    return render_template('show_lines.html',
                           lines=Lines.query.filter(Lines.operator_id == operator_id).order_by(Lines.sort_index.asc()))


@routes.route('/operator/<operator_id>/line/<line_id>', methods=["GET"])
def render_stops(operator_id, line_id):
    operator_check = check_valid_operator(operator_id)
    if operator_check is not None:
        return operator_check
    line_check = check_valid_line(operator_id, line_id)
    if line_check is not None:
        return line_check
    transit_api_key, siri_base_url = tndc.read_key_api_file()
    pattern_dict = tndc.get_pattern_dict(transit_api_key, siri_base_url, operator_id, line_id)
    tndc.save_patterns(db, operator_id, line_id, pattern_dict)
    operator_val = Operators.query.filter(Operators.operator_id == operator_id).first()
    line_val = Lines.query.filter(db.and_(Lines.operator_id == operator_id, Lines.line_id == line_id)).first()

    direction_0_id = line_val.direction_0_id
    direction_1_id = line_val.direction_1_id
    direction_0_pattern = Patterns.query.filter(db.and_(Patterns.operator_id == operator_id,
                                                        Patterns.line_id == line_id,
                                                        Patterns.pattern_direction == direction_0_id)
                                                ).order_by(Patterns.pattern_trip_count.desc()).first()
    direction_1_pattern = Patterns.query.filter(db.and_(Patterns.operator_id == operator_id,
                                                        Patterns.line_id == line_id,
                                                        Patterns.pattern_direction == direction_1_id)
                                                ).order_by(Patterns.pattern_trip_count.desc()).first()

    direction_0_stops = Stops.query.join(StopPatterns, Stops.stop_id == StopPatterns.stop_id
                                         ).filter(StopPatterns.pattern_id == direction_0_pattern.pattern_id
                                                  ).order_by(StopPatterns.stop_order.asc())
    direction_1_stops = Stops.query.join(StopPatterns, Stops.stop_id == StopPatterns.stop_id
                                         ).filter(StopPatterns.pattern_id == direction_1_pattern.pattern_id
                                                  ).order_by(StopPatterns.stop_order.asc())

    return render_template('show_stops.html',
                           direction_0_stops=direction_0_stops.all(),
                           direction_1_stops=direction_1_stops.all(),
                           operator=operator_val,
                           line=line_val)


@routes.route('/operator/<operator_id>/stop/<stop_id>', methods=["GET"])
def render_eta(operator_id, stop_id):
    operator_check = check_valid_operator(operator_id)
    if operator_check is not None:
        return operator_check
    stop_check = check_valid_stop(operator_id, stop_id)
    if stop_check is not None:
        return stop_check
    current_time = dt.datetime.now(dt.timezone.utc)
    transit_api_key, siri_base_url = tndc.read_key_api_file()
    if tndc.refresh_needed(db, operator_id, 'vehicle_monitoring_updated', VEHICLE_MONITORING_REFRESH_LIMIT):
        vehicle_monitoring_dict = tndc.get_vehicle_monitoring_dict(transit_api_key, siri_base_url, operator_id)
        tndc.save_vehicle_monitoring(db, operator_id, vehicle_monitoring_dict, current_time)
    upcoming_dict = tndc.sort_response_dict(tndc.upcoming_vehicles_vm(db, operator_id, stop_id, current_time))
    print(tndc.upcoming_vehicles_vm(db, operator_id, stop_id, current_time))
    print(upcoming_dict)
    return render_template('show_etas.html', eta_dict=upcoming_dict)


def check_valid_operator(operator_id):
    operator_val = db.session.query(Operators).first()
    if operator_val is None:
        error = 'Need to setup program before using. Please provide valid api address and api key.'
        flash(error, 'error')
        return redirect(url_for('routes.setup'))
    operator_val = Operators.query.filter(Operators.operator_id == operator_id).first()
    if operator_val is None:
        error = ('Operator {0} is not in database. Check to see if monitored '
                 'or valid operator id provided').format(operator_id)
        flash(error, 'error')
        return render_template('index.html',
                               operators=Operators.query.filter(Operators.operator_monitored).all())
    return None


def check_valid_line(operator_id, line_id):
    line_val = Lines.query.filter(db.and_(Lines.operator_id == operator_id, Lines.line_id == line_id)).first()
    if line_val is None:
        error = 'Operator {0} with line {1} is not in database.'.format(operator_id, line_id)
        return render_template('show_lines.html',
                               lines=Lines.query.filter(Lines.operator_id ==
                                                        operator_id).order_by(Lines.sort_index.asc()),
                               error=error)
    return None


def check_valid_stop(operator_id, stop_id):
    stop_val = Stops.query.filter(db.and_(Stops.operator_id == operator_id, Stops.stop_id == stop_id)).first()
    if stop_val is None:
        error = 'Operator {0} with stop {1} is not in database.'.format(operator_id, stop_id)
        return render_template('show_lines.html',
                               lines=Lines.query.filter(Lines.operator_id ==
                                                        operator_id).order_by(Lines.sort_index.asc()),
                               error=error)
    return None
