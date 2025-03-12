import pytest
import json

from transit_notification import create_app, db, db_commands
from transit_notification.models import (Operator, Vehicle, OnwardCall, Line, Stop, StopPattern, Pattern,
                                         StopTimetable, Parameter, Shape)
import datetime as dt
from tests.test_comparison_jsons import TestComparisonJsons
from collections import defaultdict, OrderedDict
import dateutil

selected_operator = 'SF'
selected_stop = '15553'
selected_line = '14'
current_time = dt.datetime(2023, 9, 26, 15, 0, 0, 0,
                           dt.timezone.utc)


def test_save_operators(app):
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_dict = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        select = db.select(Operator).filter_by(operator_id=selected_operator)
        operator = db.session.execute(select).scalar()
        assert remove_internal_keys(operator.__dict__) == \
               remove_internal_keys(TestComparisonJsons.operator_sf.__dict__)


def test_save_lines(app):
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_dict = json.load(f)
    with open("test_input_jsons/lines.json", 'r') as f:
        line_dict = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        db_commands.save_lines(db, selected_operator, line_dict, current_time)
        select = db.select(Line).filter_by(operator_id=selected_operator)
        lines = db.session.execute(select).scalars().all()
        line_cmp_dict = remove_internal_keys(TestComparisonJsons.line_14.__dict__)
        line_cmp_dict.update({'direction_0_id': None, 'direction_0_name': None, 'direction_1_id': None,
                              'direction_1_name': None})
        assert remove_internal_keys(lines[0].__dict__) == line_cmp_dict


def test_save_stops(app):
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_dict = json.load(f)
    with open("test_input_jsons/stops.json", 'r') as f:
        stop_dict = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        db_commands.save_stops(db, selected_operator, stop_dict, current_time)
        select = db.select(Stop).filter_by(operator_id=selected_operator)
        stops = db.session.execute(select).scalars().all()
        stops_cmp_dict = remove_internal_keys(TestComparisonJsons.stop_15551.__dict__)
        assert remove_internal_keys(stops[0].__dict__) == stops_cmp_dict


def test_parse_vehicle_dict():
    with open("test_input_jsons/vehicle_monitoring_modified.json", 'r') as f:
        vehicles_dict = json.load(f)
    vehicle_list = vehicles_dict["Siri"]["ServiceDelivery"]["VehicleMonitoringDelivery"]["VehicleActivity"]
    parsed_vehicle, onward_call = db_commands.parse_vehicle_dict(selected_operator, vehicle_list[0])
    assert remove_internal_keys(parsed_vehicle.__dict__) == \
           remove_internal_keys(TestComparisonJsons.vehicle_0.__dict__)


def test_onward_call():
    with open("test_input_jsons/vehicle_monitoring_modified.json", 'r') as f:
        vehicles_dict = json.load(f)
    vehicle_list = vehicles_dict["Siri"]["ServiceDelivery"]["VehicleMonitoringDelivery"]["VehicleActivity"]
    vehicle = vehicle_list[0]
    vehicle_journey_ref = vehicle['MonitoredVehicleJourney']['FramedVehicleJourneyRef']['DatedVehicleJourneyRef']
    dataframe_ref = vehicle['MonitoredVehicleJourney']['FramedVehicleJourneyRef']['DataFrameRef']
    onward_calls = db_commands.parse_vehicle_calls(selected_operator,
                                                   vehicle_journey_ref,
                                                   dataframe_ref,
                                                   vehicle_list[0]["MonitoredVehicleJourney"])
    assert len(onward_calls) == 18
    assert remove_internal_keys(onward_calls[-1].__dict__) == \
           remove_internal_keys(TestComparisonJsons.vehicle_onward_calls[0].__dict__)
    assert remove_internal_keys(onward_calls[0].__dict__) == \
           remove_internal_keys(TestComparisonJsons.vehicle_onward_calls[1].__dict__)


def test_save_vehicle_monitoring(app):
    with open("test_input_jsons/vehicle_monitoring_modified.json", 'r') as f:
        vehicles_dict = json.load(f)
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_dict = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        db_commands.save_vehicle_monitoring(db, selected_operator, vehicles_dict, current_time)
        select = db.select(Vehicle).filter_by(operator_id=selected_operator)
        vehicle = db.session.execute(select).scalars().all()
        assert remove_internal_keys(vehicle[0].__dict__) == \
               remove_internal_keys(TestComparisonJsons.vehicle_0.__dict__)
        assert remove_internal_keys(vehicle[1].__dict__) == \
               remove_internal_keys(TestComparisonJsons.vehicle_1.__dict__)
        assert remove_internal_keys(vehicle[2].__dict__) == \
               remove_internal_keys(TestComparisonJsons.vehicle_2.__dict__)
        select = db.select(OnwardCall).filter_by(operator_id=selected_operator)
        onward_calls = db.session.execute(select).scalars().all()
        assert len(onward_calls) == 106
        select = db.select(OnwardCall).filter_by(operator_id=selected_operator, vehicle_journey_ref="Schedule_0-Est_0",
                                                 stop_id="15553")
        onward_calls = db.session.execute(select).scalars().all()
        assert remove_internal_keys(onward_calls[0].__dict__) == \
               remove_internal_keys(TestComparisonJsons.vehicle_onward_calls[0].__dict__)


def test_upcoming_vehicles(app):

    with open("test_input_jsons/vehicle_monitoring_modified.json", 'r') as f:
        vehicles_dict = json.load(f)
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_dict = json.load(f)
    with open("test_input_jsons/lines.json", 'r') as f:
        line_dict = json.load(f)
    with open("test_input_jsons/stops.json", 'r') as f:
        stop_dict = json.load(f)
    with open("test_input_jsons/patterns.json", 'r') as f:
        pattern_dict = json.load(f)
    with open("test_input_jsons/stop_timetable_15553.json", 'r') as f:
        stop_timetable = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        db_commands.save_lines(db, selected_operator, line_dict, current_time)
        db_commands.save_stops(db, selected_operator, stop_dict, current_time)
        db_commands.save_patterns(db, selected_operator, selected_line, pattern_dict)
        db_commands.save_stop_timetable(db, selected_operator, selected_stop, stop_timetable)
        db_commands.save_vehicle_monitoring(db, selected_operator, vehicles_dict, current_time)
        upcoming_dict = db_commands.upcoming_vehicles(db, selected_operator, selected_stop, current_time)
        assert upcoming_dict == TestComparisonJsons.upcoming_vehicles


def test_save_stop_pattern(app):
    with open("test_input_jsons/patterns.json", 'r') as f:
        pattern_dict = json.load(f)
    pattern = pattern_dict['journeyPatterns'][0]
    pattern_id = pattern['serviceJourneyPatternRef']
    with app.app_context():
        db_commands.save_stop_pattern(db, selected_operator, pattern_id, pattern['PointsInSequence'])
        select = db.select(StopPattern).filter_by(operator_id=selected_operator, pattern_id=pattern_id)
        stop_patterns = db.session.execute(select).scalars().all()
        assert len(stop_patterns) == 25
        assert remove_internal_keys(stop_patterns[0].__dict__) == \
               remove_internal_keys(TestComparisonJsons.stop_pattern_1.__dict__)


def test_save_patterns(app):
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_dict = json.load(f)
    with open("test_input_jsons/lines.json", 'r') as f:
        line_dict = json.load(f)
    with open("test_input_jsons/stops.json", 'r') as f:
        stop_dict = json.load(f)
    with open("test_input_jsons/patterns.json", 'r') as f:
        pattern_dict = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        db_commands.save_lines(db, selected_operator, line_dict, current_time)
        db_commands.save_stops(db, selected_operator, stop_dict, current_time)
        db_commands.save_patterns(db, selected_operator, selected_line, pattern_dict)
        select = db.select(Pattern).filter_by(operator_id=selected_operator, line_id=selected_line)
        patterns = db.session.execute(select).scalars().all()
        assert len(patterns) == 9
        assert remove_internal_keys(patterns[0].__dict__) == \
               remove_internal_keys(TestComparisonJsons.pattern_1.__dict__)


def test_stop_timetable(app):
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_dict = json.load(f)
    with open("test_input_jsons/lines.json", 'r') as f:
        line_dict = json.load(f)
    with open("test_input_jsons/stops.json", 'r') as f:
        stop_dict = json.load(f)
    with open("test_input_jsons/patterns.json", 'r') as f:
        pattern_dict = json.load(f)
    with open("test_input_jsons/stop_timetable_15553.json", 'r') as f:
        stop_timetable = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        db_commands.save_lines(db, selected_operator, line_dict, current_time)
        db_commands.save_stops(db, selected_operator, stop_dict, current_time)
        db_commands.save_patterns(db, selected_operator, '49', pattern_dict)
        db_commands.save_stop_timetable(db, selected_operator, selected_stop, stop_timetable)
        select = db.select(StopTimetable).filter_by(operator_id=selected_operator,
                                                    vehicle_journey_ref="Schedule_0-Est_0",
                                                    stop_id=selected_stop)
        stop_timetable = db.session.execute(select).scalars().all()
        assert len(stop_timetable) == 1
        assert remove_internal_keys(stop_timetable[0].__dict__) == \
               remove_internal_keys(TestComparisonJsons.stop_timetable_1.__dict__)


def test_parse_stop_monitoring_dict():
    with open("test_input_jsons/stop_monitoring_15553.json", 'r') as f:
        stop_monitoring_dict = json.load(f)
    monitored_stop_visit = stop_monitoring_dict['ServiceDelivery']['StopMonitoringDelivery']['MonitoredStopVisit'][0]
    vehicle, onward_call = db_commands.parse_stop_monitoring_dict(selected_operator, monitored_stop_visit)
    assert (remove_internal_keys(vehicle.__dict__) ==
            remove_internal_keys(TestComparisonJsons.stop_monitoring_vehicle.__dict__))
    assert remove_internal_keys(onward_call.__dict__) == \
           remove_internal_keys(TestComparisonJsons.stop_monitoring_onward_call.__dict__)


def test_save_stop_monitoring(app):
    with open("test_input_jsons/stop_monitoring_15553.json", 'r') as f:
        stop_monitoring_dict = json.load(f)
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_dict = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        db_commands.save_stop_monitoring(db, selected_operator, stop_monitoring_dict, current_time)
        select = db.select(Vehicle).filter_by(operator_id=selected_operator)
        vehicle = db.session.execute(select).scalars().all()
        assert len(vehicle) == 5
        assert remove_internal_keys(vehicle[0].__dict__) == \
               remove_internal_keys(TestComparisonJsons.stop_monitoring_vehicle.__dict__)
        select = db.select(OnwardCall).filter_by(operator_id=selected_operator)
        onward_calls = db.session.execute(select).scalars().all()
        assert len(onward_calls) == 6
        select = db.select(OnwardCall).filter_by(operator_id=selected_operator, vehicle_journey_ref="Schedule_0-Est_0",
                                                 stop_id="15553")
        onward_calls = db.session.execute(select).scalars().all()
        assert remove_internal_keys(onward_calls[0].__dict__) == \
               remove_internal_keys(TestComparisonJsons.stop_monitoring_onward_call.__dict__)


def test_stop_monitoring_etas(app):
    with open("test_input_jsons/stop_monitoring_15553.json", 'r') as f:
        stop_monitoring_dict = json.load(f)
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_dict = json.load(f)
    with open("test_input_jsons/lines.json", 'r') as f:
        line_dict = json.load(f)
    with open("test_input_jsons/stops.json", 'r') as f:
        stop_dict = json.load(f)
    with open("test_input_jsons/patterns.json", 'r') as f:
        pattern_dict = json.load(f)
    with open("test_input_jsons/stop_timetable_15553.json", 'r') as f:
        stop_timetable = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        db_commands.save_lines(db, selected_operator, line_dict, current_time)
        db_commands.save_stops(db, selected_operator, stop_dict, current_time)
        db_commands.save_patterns(db, selected_operator, selected_line, pattern_dict)
        db_commands.save_stop_timetable(db, selected_operator, selected_stop, stop_timetable)
        db_commands.save_stop_monitoring(db, selected_operator, stop_monitoring_dict, current_time)
        upcoming_dict = db_commands.upcoming_vehicles(db, selected_operator, selected_stop, current_time)
        assert upcoming_dict == TestComparisonJsons.stop_monitoring_upcoming_vehicles

def test_determine_vehicle_ref_full_journey(app):
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_dict = json.load(f)
    with open("test_input_jsons/lines.json", 'r') as f:
        line_dict = json.load(f)
    with open("test_input_jsons/stops.json", 'r') as f:
        stop_dict = json.load(f)
    with open("test_input_jsons/patterns.json", 'r') as f:
        pattern_dict = json.load(f)
    with open("test_input_jsons/stop_timetable_15553.json", 'r') as f:
        stop_timetable_15553 = json.load(f)
    with open("test_input_jsons/stop_timetable_15557.json", 'r') as f:
        stop_timetable_15557 = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        db_commands.save_lines(db, selected_operator, line_dict, current_time)
        db_commands.save_stops(db, selected_operator, stop_dict, current_time)
        db_commands.save_patterns(db, selected_operator, selected_line, pattern_dict)
        db_commands.save_stop_timetable(db, selected_operator, '15553', stop_timetable_15553)
        db_commands.save_stop_timetable(db, selected_operator, '15557', stop_timetable_15557)

        stmt = db.select('*').select_from(StopTimetable)
        result = db.session.execute(stmt).fetchall()
        print('\n')
        print(result)

        full_journey_vehicle = db_commands.determine_vehicle_ref_full_journey(db,'SF', '15553', '15557')
        print(full_journey_vehicle)
        print(type(full_journey_vehicle))
        assert full_journey_vehicle == 'Schedule_0-Est_0'


def test_refresh_limit(app):
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_dict = json.load(f)
    with open("test_input_jsons/lines.json", 'r') as f:
        line_dict = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        assert db_commands.refresh_needed(db, selected_operator, 'lines_updated', 1, current_time) is True
        db_commands.save_lines(db, selected_operator, line_dict, current_time)
        assert db_commands.refresh_needed(db, selected_operator, 'lines_updated', 1, current_time) is False
        assert db_commands.refresh_needed(db, selected_operator, 'lines_updated', 1, current_time+dt.timedelta(seconds=61)) is True


def test_format_eta_time():
    assert db_commands.format_eta_time(dt.timedelta(seconds=59)) == "Arriving"
    assert db_commands.format_eta_time(dt.timedelta(seconds=61)) == "1 min"
    assert db_commands.format_eta_time(dt.timedelta(seconds=119)) == "1 min"
    assert db_commands.format_eta_time(dt.timedelta(seconds=121)) == "2 mins"
    assert db_commands.format_eta_time(dt.timedelta(minutes=121)) == "121 mins"
    assert db_commands.format_eta_time(dt.timedelta(days=1, minutes=1)) == "1441 mins"
    assert db_commands.format_eta_time(dt.timedelta(days=-1, minutes=1)) == "-1439 mins"
    assert db_commands.format_eta_time(dt.timedelta(days=-7, hours=18, minutes=59, seconds=46)) == "-8941 mins"


def test_sort_response_dict():
    test_dict = defaultdict(list)
    test_dict['1'] = ["5 mins", "Arriving", "20 mins"]
    test_dict['F'] = ["12 mins", "2 mins"]
    test_dict['2'] = ["Arriving", "5 mins"]
    expected_dict = OrderedDict([('1', 'Arriving, 5 mins, 20 mins'),
                                 ('2', 'Arriving, 5 mins'),
                                 ('F', '2 mins, 12 mins')])
    assert db_commands.sort_response_dict(test_dict) == expected_dict


def test_parse_time_str():
    assert db_commands.parse_time_str(None) is None
    assert db_commands.parse_time_str('2022-12-26') == dt.datetime(2022, 12, 26)
    assert db_commands.parse_time_str('2022-12-27T06:06:05Z') == dt.datetime(2022, 12, 27, 6, 6, 5)
    assert db_commands.parse_time_str('2022-12-27T06:06:05Z') == dt.datetime(2022, 12, 27, 6, 6, 5)
    assert db_commands.parse_time_str('2023-09-21T07:00:29-07:00') == dt.datetime(2023, 9, 21, 14, 0, 29)


def test_parse_optional_floats():
    assert db_commands.parse_optional_floats('3.14') == 3.14
    assert db_commands.parse_optional_floats('') is None


def test_parse_bools():
    assert db_commands.parse_bools(True) is True
    assert db_commands.parse_bools('true') is True
    assert db_commands.parse_bools(False) is False
    assert db_commands.parse_bools('false') is False
    assert db_commands.parse_bools('') is False
    with pytest.raises(ValueError) as e_info:
        db_commands.parse_bools('test') is False
    assert str(e_info.value) == 'parse_bools expected true or false, got test'


def remove_internal_keys(input_dict):
    keys_to_remove = [key for key in input_dict.keys() if key.startswith("_")]
    for key in keys_to_remove:
        input_dict.pop(key, None)
    return input_dict


def test_operator_refresh_needed(app):
    with app.app_context():
        assert db_commands.operator_refresh_needed(db, 1, current_time) is True
        operator_refresh = Parameter("operator_refresh_time", current_time.isoformat())
        db.session.add(operator_refresh)
        db.session.commit()
        assert db_commands.operator_refresh_needed(db, 1, current_time + dt.timedelta(minutes=0.5)) is False
        assert db_commands.operator_refresh_needed(db, 1, current_time + dt.timedelta(minutes=1.5)) is True


def test_save_operator_refresh_time(app):
    with app.app_context():
        db_commands.save_operator_refresh_time(db, current_time)
        operator_refresh_time = db.session.execute(db.select(Parameter).filter_by(
            name="operator_refresh_time")).scalar_one_or_none()
        last_update_time = dateutil.parser.isoparse(operator_refresh_time.value).replace(tzinfo=None)
        assert last_update_time == current_time.replace(tzinfo=None)

def test_save_shape(app):
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_dict = json.load(f)
    with open("test_input_jsons/lines.json", 'r') as f:
        line_dict = json.load(f)
    with open("test_input_jsons/shape.json", 'r') as f:
        shape_dict = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        db_commands.save_lines(db, selected_operator, line_dict, current_time)
        db_commands.save_shapes(db, selected_operator, selected_line, shape_dict, current_time)
        select = db.select(Shape).filter_by(operator_id=selected_operator,
                                            line_id=selected_line
                                            )
        shape = db.session.execute(select).scalars().all()
        print(shape)
        assert True == False
        assert len(shape) == 5
        assert remove_internal_keys(shape[0].__dict__) == \
               remove_internal_keys(TestComparisonJsons.route_shape)



