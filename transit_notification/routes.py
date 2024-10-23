from flask import Blueprint, render_template, redirect, url_for, flash
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


@routes.route('/setup')
def setup():
    error = None
    return render_template('setup.html', error=error)


@routes.route('/')
def index():
    error = None
    return render_template('index.html', error=error)


@routes.route('/operators')
def show_operators():
    transit_api_key, siri_base_url = tndc.read_key_api_file()
    operator_val = db.session.execute(db.select(Operator)).first()
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

    return render_template('show_operators.html',
                           operators=db.session.execute(
                               db.select(Operator).filter(Operator.operator_monitored)).scalars().all())


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
    lines = db.session.execute(
        db.select(Line).filter(Line.operator_id == operator_id).order_by(Line.sort_index.asc())).scalars().all()
    return render_template('show_lines.html',
                           lines=lines)


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

    operator_val = db.session.execute(db.select(Operator)).first()
    line_val = db.session.execute(db.select(Line).filter(
        db.and_(Line.operator_id == operator_id, Line.line_id == line_id))).scalar()

    direction_0_id = line_val.direction_0_id
    direction_0_pattern = db.session.execute(db.select(Pattern).filter(
        db.and_(Pattern.operator_id == operator_id,
                Pattern.line_id == line_id,
                Pattern.pattern_direction == direction_0_id)).order_by(Pattern.pattern_trip_count.desc())).scalar()
    direction_0_stops = db.session.execute(
        db.select(Stop, StopPattern).join(StopPattern, Stop.stop_id == StopPattern.stop_id
                                          ).filter(StopPattern.pattern_id == direction_0_pattern.pattern_id
                                                   ).order_by(StopPattern.stop_order.asc())).scalars().all()
    direction_1_id = line_val.direction_1_id
    if direction_1_id is None:
        return render_template('show_stops_single_direction.html',
                               direction_0_stops=direction_0_stops,
                               operator=operator_val,
                               line=line_val)

    direction_1_pattern = db.session.execute(db.select(Pattern).filter(
        db.and_(Pattern.operator_id == operator_id,
                Pattern.line_id == line_id,
                Pattern.pattern_direction == direction_1_id)).order_by(Pattern.pattern_trip_count.desc())).scalar()
    direction_1_stops = db.session.execute(
        db.select(Stop, StopPattern).join(StopPattern, Stop.stop_id == StopPattern.stop_id
                                          ).filter(StopPattern.pattern_id == direction_1_pattern.pattern_id
                                                   ).order_by(StopPattern.stop_order.asc())).scalars().all()


    return render_template('show_stops.html',
                           direction_0_stops=direction_0_stops,
                           direction_1_stops=direction_1_stops,
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
    operator_val = db.session.execute(db.select(Operator)).scalars()
    if operator_val is None:
        error = 'Please use links instead of directly typing web address.'
        flash(error, 'error')
        return redirect(url_for('routes.show_operators'))
    operator_val = db.session.execute(db.select(Operator).filter(Operator.operator_id == operator_id)).scalar_one_or_none()
    if operator_val is None:
        error = ('Operator {0} is not in database or database not initialized. Check to see if monitored '
                 'or valid operator id is below.').format(operator_id)
        flash(error, 'error')
        return redirect(url_for('routes.show_operators'))
    return None


def check_valid_line(operator_id, line_id):
    line_val = db.session.execute(
        db.select(Line).filter(Line.operator_id == operator_id and Line.line_id == line_id).order_by(
            Line.sort_index.asc())).scalar()
    if line_val is None:
        error = 'Operator {0} with line {1} is not in database.'.format(operator_id, line_id)
        lines = db.session.execute(
            db.select(Line).filter(Line.operator_id == operator_id).order_by(Line.sort_index.asc())).scalars().all()
        return render_template('show_lines.html',
                               lines=lines,
                               error=error)
    return None


def check_valid_stop(operator_id, stop_id):
    stop_val = db.session.execute(
        db.select(Stop).filter(Stop.operator_id == operator_id and Stop.stop_id == stop_id)).scalar()
    if stop_val is None:
        error = 'Operator {0} with stop {1} is not in database.'.format(operator_id, stop_id)
        lines = db.session.execute(
            db.select(Line).filter(Line.operator_id == operator_id).order_by(Line.sort_index.asc())).scalars().all()
        return render_template('show_lines.html',
                               lines=lines,
                               error=error)
    return None
