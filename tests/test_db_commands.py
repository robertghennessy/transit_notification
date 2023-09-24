import pytest
import json

from transit_notification import create_app, db, db_commands
from transit_notification.models import (Operators, Vehicles, OnwardCalls, Lines, Stops, StopPatterns, Patterns,
                                         StopTimetable)
import datetime as dt
from dateutil.tz import tzutc
from tests.test_comparison_jsons import TestComparisonJsons
from collections import defaultdict, OrderedDict

selected_operator = 'SF'
selected_stop = '15553'
selected_line = '14'

def test_save_operators(app):
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_dict = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        select = db.select(Operators).filter_by(operator_id=selected_operator)
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
        db_commands.save_lines(db, selected_operator, line_dict, dt.datetime.utcnow())
        select = db.select(Lines).filter_by(operator_id=selected_operator)
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
        db_commands.save_stops(db, selected_operator, stop_dict, dt.datetime.utcnow())
        select = db.select(Stops).filter_by(operator_id=selected_operator)
        stops = db.session.execute(select).scalars().all()
        stops_cmp_dict = remove_internal_keys(TestComparisonJsons.stop_13230.__dict__)
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
    assert len(onward_calls) == 16
    assert remove_internal_keys(onward_calls[0].__dict__) == \
           remove_internal_keys(TestComparisonJsons.vehicle_onward_calls[0].__dict__)
    assert remove_internal_keys(onward_calls[-1].__dict__) == \
           remove_internal_keys(TestComparisonJsons.vehicle_onward_calls[1].__dict__)


def test_save_vehicle_monitoring(app):
    with open("test_input_jsons/vehicle_monitoring_modified.json", 'r') as f:
        vehicles_dict = json.load(f)
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_dict = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        db_commands.save_vehicle_monitoring(db, selected_operator, vehicles_dict, dt.datetime.utcnow())
        select = db.select(Vehicles).filter_by(operator_id=selected_operator)
        vehicle = db.session.execute(select).scalars().all()
        assert remove_internal_keys(vehicle[0].__dict__) == \
               remove_internal_keys(TestComparisonJsons.vehicle_0.__dict__)
        assert remove_internal_keys(vehicle[1].__dict__) == \
               remove_internal_keys(TestComparisonJsons.vehicle_1.__dict__)
        assert remove_internal_keys(vehicle[2].__dict__) == \
               remove_internal_keys(TestComparisonJsons.vehicle_2.__dict__)
        select = db.select(OnwardCalls).filter_by(operator_id=selected_operator)
        onward_calls = db.session.execute(select).scalars().all()
        assert len(onward_calls) == 124
        select = db.select(OnwardCalls).filter_by(operator_id=selected_operator, vehicle_journey_ref="Schedule_0-Est_0",
                                                  stop_id="15551")
        onward_calls = db.session.execute(select).scalars().all()
        assert remove_internal_keys(onward_calls[0].__dict__) == \
               remove_internal_keys(TestComparisonJsons.vehicle_onward_calls[0].__dict__)


def test_upcoming_vehicles(app):
    current_time = dt.datetime(2023, 9, 21, 14, 0, 23, 0,
                               dt.timezone.utc)
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
    with open("test_input_jsons/stop_timetable_modified.json", 'r') as f:
        stop_timetable = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        db_commands.save_lines(db, selected_operator, line_dict, dt.datetime.utcnow())
        db_commands.save_stops(db, selected_operator, stop_dict, dt.datetime.utcnow())
        db_commands.save_patterns(db, selected_operator, selected_line, pattern_dict)
        db_commands.stop_timetable(db, selected_operator, selected_stop, stop_timetable)
        db_commands.save_vehicle_monitoring(db, selected_operator, vehicles_dict, current_time)
        upcoming_dict = db_commands.upcoming_vehicles_vm(db, selected_operator, selected_stop, current_time)
        assert upcoming_dict == TestComparisonJsons.upcoming_vehicles


def test_save_stop_pattern(app):
    with open("test_input_jsons/patterns.json", 'r') as f:
        pattern_dict = json.load(f)
    pattern = pattern_dict['journeyPatterns'][0]
    pattern_id = pattern['serviceJourneyPatternRef']
    with app.app_context():
        db_commands.save_stop_pattern(db, selected_operator, pattern_id, pattern['PointsInSequence'])
        select = db.select(StopPatterns).filter_by(operator_id=selected_operator, pattern_id=pattern_id)
        stop_patterns = db.session.execute(select).scalars().all()
        assert len(stop_patterns) == 46
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
        db_commands.save_lines(db, selected_operator, line_dict, dt.datetime.utcnow())
        db_commands.save_stops(db, selected_operator, stop_dict, dt.datetime.utcnow())
        db_commands.save_patterns(db, selected_operator, selected_line, pattern_dict)
        select = db.select(Patterns).filter_by(operator_id=selected_operator, line_id=selected_line)
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
    with open("test_input_jsons/stop_timetable_modified.json", 'r') as f:
        stop_timetable = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, operators_dict)
        db_commands.save_lines(db, selected_operator, line_dict, dt.datetime.utcnow())
        db_commands.save_stops(db, selected_operator, stop_dict, dt.datetime.utcnow())
        db_commands.save_patterns(db, selected_operator, '49', pattern_dict)
        db_commands.stop_timetable(db, selected_operator, selected_stop, stop_timetable)
        select = db.select(StopTimetable).filter_by(operator_id=selected_operator,
                                                    vehicle_journey_ref="Schedule_0-Est_0",
                                                    stop_id=selected_stop)
        stop_timetable = db.session.execute(select).scalars().all()
        assert len(stop_timetable) == 1
        assert remove_internal_keys(stop_timetable[0].__dict__) == \
               remove_internal_keys(TestComparisonJsons.stop_timetable_1.__dict__)


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


def remove_internal_keys(input_dict):
    keys_to_remove = [key for key in input_dict.keys() if key.startswith("_")]
    for key in keys_to_remove:
        input_dict.pop(key, None)
    return input_dict


def test_parse_time_str():
    assert db_commands.parse_time_str(None) is None
    assert db_commands.parse_time_str('2022-12-26') == dt.datetime(2022, 12, 26)
    assert db_commands.parse_time_str('2022-12-27T06:06:05Z') == dt.datetime(2022, 12, 27, 6, 6, 5)
    assert db_commands.parse_time_str('2022-12-27T06:06:05Z') == dt.datetime(2022, 12, 27, 6, 6, 5)
    assert db_commands.parse_time_str('2023-09-21T07:00:29-07:00') == dt.datetime(2023, 9, 21, 14, 0, 29)

