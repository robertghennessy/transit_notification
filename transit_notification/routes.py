from flask import Blueprint, render_template, request, redirect, url_for, flash
from transit_notification import db
from transit_notification.models import Operator, Line, Pattern, StopPattern, Stop
import siri_transit_api_client
import datetime as dt
import transit_notification.db_commands as tndc

routes = Blueprint('routes', __name__)

# units are minutes
OPERATORS_REFRESH_LIMIT = 24*60
LINES_REFRESH_LIMIT = 24*60
STOPS_REFRESH_LIMIT = 24*60
PATTERN_REFRESH_LIMIT = 24*60
VEHICLE_MONITORING_REFRESH_LIMIT = 1
STOP_MONITORING_REFRESH_LIMIT = 1


@routes.route('/setup', methods=('GET', 'POST'))
def setup():
    error = None
    return render_template('setup.html', error=error)


@routes.route('/')
def index():
    transit_api_key, siri_base_url = tndc.read_key_api_file()
    operator_val = db.session.query(Operator).first()
    current_time = dt.datetime.now(dt.timezone.utc)
    operator_refresh_needed = tndc.operator_refresh_needed(db, OPERATORS_REFRESH_LIMIT, current_time)

    if operator_val is None or operator_refresh_needed:
        try:
            operators_json = tndc.get_operators_dict(transit_api_key=transit_api_key, siri_base_url=siri_base_url)
            tndc.save_operators(db, operators_json)
            tndc.save_operator_refresh_time(db, current_time)
        except siri_transit_api_client.exceptions.TransportError:
            error = 'Unable to establish connection to {0}. Please check url and resubmit.'.format(siri_base_url)
            return render_template('setup.html', error=error)
        except siri_transit_api_client.exceptions.ApiError:
            error = 'This API key provided is invalid.'
            return render_template('setup.html', error=error)

    return render_template('index.html',
                           operators=Operator.query.filter(Operator.operator_monitored).all())


@routes.route('/operator/<operator_id>', methods=["GET"])
def render_lines(operator_id):
    operator_check = check_valid_operator(operator_id)
    if operator_check is not None:
        return operator_check
    current_time = dt.datetime.now(dt.timezone.utc)
    transit_api_key, siri_base_url = tndc.read_key_api_file()
    if tndc.refresh_needed(db, operator_id, 'lines_updated', LINES_REFRESH_LIMIT, current_time):
        lines_dict = tndc.get_lines_dict(transit_api_key, siri_base_url, operator_id)
        tndc.save_lines(db, operator_id, lines_dict, current_time)
    return render_template('show_lines.html',
                           lines=Line.query.filter(Line.operator_id == operator_id).order_by(Line.sort_index.asc()))


@routes.route('/operator/<operator_id>/line/<line_id>', methods=["GET"])
def render_stops(operator_id, line_id):
    operator_check = check_valid_operator(operator_id)
    if operator_check is not None:
        return operator_check
    line_check = check_valid_line(operator_id, line_id)
    if line_check is not None:
        return line_check
    current_time = dt.datetime.now(dt.timezone.utc)
    transit_api_key, siri_base_url = tndc.read_key_api_file()
    if tndc.refresh_needed(db, operator_id, 'stops_updated', STOPS_REFRESH_LIMIT, current_time):
        stops_dict = tndc.get_stops_dict(transit_api_key, siri_base_url, operator_id)
        tndc.save_stops(db, operator_id, stops_dict, current_time)
    if tndc.refresh_needed(db, operator_id, 'patterns_updated', PATTERN_REFRESH_LIMIT, current_time):
        pattern_dict = tndc.get_pattern_dict(transit_api_key, siri_base_url, operator_id, line_id)
        tndc.save_patterns(db, operator_id, line_id, pattern_dict)

    operator_val = Operator.query.filter(Operator.operator_id == operator_id).first()
    line_val = Line.query.filter(db.and_(Line.operator_id == operator_id, Line.line_id == line_id)).first()

    direction_0_id = line_val.direction_0_id
    direction_1_id = line_val.direction_1_id
    direction_0_pattern = Pattern.query.filter(db.and_(Pattern.operator_id == operator_id,
                                                       Pattern.line_id == line_id,
                                                       Pattern.pattern_direction == direction_0_id)
                                               ).order_by(Pattern.pattern_trip_count.desc()).first()
    direction_1_pattern = Pattern.query.filter(db.and_(Pattern.operator_id == operator_id,
                                                       Pattern.line_id == line_id,
                                                       Pattern.pattern_direction == direction_1_id)
                                               ).order_by(Pattern.pattern_trip_count.desc()).first()

    direction_0_stops = Stop.query.join(StopPattern, Stop.stop_id == StopPattern.stop_id
                                        ).filter(StopPattern.pattern_id == direction_0_pattern.pattern_id
                                                 ).order_by(StopPattern.stop_order.asc())
    direction_1_stops = Stop.query.join(StopPattern, Stop.stop_id == StopPattern.stop_id
                                        ).filter(StopPattern.pattern_id == direction_1_pattern.pattern_id
                                                 ).order_by(StopPattern.stop_order.asc())

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
    if tndc.refresh_needed(db, operator_id, 'stop_monitoring_updated', STOP_MONITORING_REFRESH_LIMIT, current_time):
        stop_monitoring_dict = tndc.get_stop_monitoring_dict(transit_api_key, siri_base_url, operator_id)
        tndc.save_stop_monitoring(db, operator_id, stop_monitoring_dict, current_time)

    upcoming_dict = tndc.sort_response_dict(tndc.upcoming_vehicles(db, operator_id, stop_id, current_time))
    return render_template('show_etas.html', eta_dict=upcoming_dict)


def check_valid_operator(operator_id: str):
    operator_val = db.session.query(Operator).first()
    if operator_val is None:
        error = 'Please use links instead of directly typing web address.'
        flash(error, 'error')
        return redirect(url_for('routes.index'))
    operator_val = Operator.query.filter(Operator.operator_id == operator_id).first()
    if operator_val is None:
        error = ('Operator {0} is not in database. Check to see if monitored '
                 'or valid operator id provided').format(operator_id)
        flash(error, 'error')
        return render_template('index.html',
                               operators=Operator.query.filter(Operator.operator_monitored).all())
    return None


def check_valid_line(operator_id, line_id):
    line_val = Line.query.filter(db.and_(Line.operator_id == operator_id, Line.line_id == line_id)).first()
    if line_val is None:
        error = 'Operator {0} with line {1} is not in database.'.format(operator_id, line_id)
        return render_template('show_lines.html',
                               lines=Line.query.filter(Line.operator_id ==
                                                       operator_id).order_by(Line.sort_index.asc()),
                               error=error)
    return None


def check_valid_stop(operator_id, stop_id):
    stop_val = Stop.query.filter(db.and_(Stop.operator_id == operator_id, Stop.stop_id == stop_id)).first()
    if stop_val is None:
        error = 'Operator {0} with stop {1} is not in database.'.format(operator_id, stop_id)
        return render_template('show_lines.html',
                               lines=Line.query.filter(Line.operator_id ==
                                                       operator_id).order_by(Line.sort_index.asc()),
                               error=error)
    return None
