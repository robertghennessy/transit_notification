import datetime as dt
from transit_notification.models import (Operator, Vehicle, OnwardCall, Line, Stop, StopPattern, Pattern,
                                         StopTimetable)
import transit_notification.db_commands


class TestComparisonJsons:
    operator_sf = Operator(
        operator_id="SF",
        operator_name="San Francisco Municipal Transportation Agency",
        operator_monitored=True,
        lines_updated=None,
        stops_updated=None,
        patterns_updated=None,
        stop_monitoring_updated=None,
        vehicle_monitoring_updated=None
    )

    line_14 = Line(line_id='14', operator_id='SF', line_name="MISSION", line_monitored=True, sort_index=0)
    line_49 = Line(line_id='49', operator_id='SF', line_name="VAN NESS-MISSION", line_monitored=True, sort_index=1)

    stop_15551 = Stop(operator_id='SF', stop_id='15551', stop_latitude=37.765125, stop_longitude=-122.419668,
                      stop_name='Mission St & 16th St')
    stop_15553 = Stop(operator_id='SF', stop_id='15553', stop_latitude=37.762635, stop_longitude=-122.419348,
                      stop_name="Mission St & 18th St")

    vehicle_0 = Vehicle(
        dataframe_ref_date=dt.date(2023, 9, 26),
        line_id='14',
        operator_id='SF',
        vehicle_direction='IB',
        vehicle_journey_ref='Schedule_0-Est_0',
        vehicle_latitude=37.7155266,
        vehicle_longitude=-122.441704,
        vehicle_bearing=30.0
    )

    vehicle_1 = Vehicle(
        dataframe_ref_date=dt.date(2023, 9, 26),
        line_id='14',
        operator_id='SF',
        vehicle_direction='IB',
        vehicle_journey_ref='Schedule_10-Est_13',
        vehicle_latitude=37.7155266,
        vehicle_longitude=-122.441704,
        vehicle_bearing=30.0
    )

    vehicle_2 = Vehicle(
        dataframe_ref_date=dt.date(2023, 9, 26),
        line_id='14',
        operator_id='SF',
        vehicle_direction='IB',
        vehicle_journey_ref='Schedule_20-Est_16',
        vehicle_latitude=37.7155266,
        vehicle_longitude=-122.441704,
        vehicle_bearing=30.0
    )

    vehicle_onward_calls = [
        OnwardCall(
                operator_id='SF',
                vehicle_journey_ref='Schedule_0-Est_0',
                dataframe_ref_date=transit_notification.db_commands.parse_time_str('2023-09-26').date(),
                stop_id='15553',
                vehicle_at_stop=True,
                aimed_arrival_time_utc=transit_notification.db_commands.parse_time_str('2023-09-26T15:00:00Z'),
                expected_arrival_time_utc=transit_notification.db_commands.parse_time_str('2023-09-26T15:00:00Z'),
                aimed_departure_time_utc=transit_notification.db_commands.parse_time_str('2023-09-26T15:00:00Z'),
                expected_departure_time_utc=transit_notification.db_commands.parse_time_str(None)
        ),
        OnwardCall(
            operator_id='SF',
            vehicle_journey_ref='Schedule_0-Est_0',
            dataframe_ref_date=transit_notification.db_commands.parse_time_str('2023-09-26').date(),
            stop_id='15551',
            vehicle_at_stop=False,
            aimed_arrival_time_utc=transit_notification.db_commands.parse_time_str("2023-09-26T15:01:28Z"),
            expected_arrival_time_utc=transit_notification.db_commands.parse_time_str("2023-09-26T15:01:41Z"),
            aimed_departure_time_utc=transit_notification.db_commands.parse_time_str("2023-09-26T15:01:28Z"),
            expected_departure_time_utc=transit_notification.db_commands.parse_time_str(None)
        )
    ]

    stop_pattern_1 = StopPattern(
        operator_id='SF',
        pattern_id=219280,
        stop_order=1,
        stop_id="15568",
        timing_point=True
    )

    pattern_1 = Pattern(
        operator_id='SF',
        line_id='14',
        pattern_id=219278,
        pattern_name='Mission St & San Jose Ave',
        pattern_direction='OB',
        pattern_trip_count=673
    )

    stop_timetable_1 = StopTimetable(
        operator_id='SF',
        vehicle_journey_ref='Schedule_0-Est_0',
        stop_id='15553',
        aimed_arrival_time_utc=dt.datetime(2023, 9, 26, 15, 0, 0),
        aimed_departure_time_utc=dt.datetime(2023, 9, 26, 15, 0, 0)
    )

    upcoming_vehicles = {
        "14": [transit_notification.db_commands.format_eta_time(dt.timedelta(minutes=0)),
               transit_notification.db_commands.format_eta_time(dt.timedelta(minutes=13)),
               transit_notification.db_commands.format_eta_time(dt.timedelta(minutes=16)),
               transit_notification.db_commands.format_eta_time(dt.timedelta(minutes=40))
               ]
    }

    stop_monitoring_vehicle = Vehicle(
        operator_id='SF',
        vehicle_journey_ref='Schedule_0-Est_0',
        dataframe_ref_date=dt.date(2023, 9, 26),
        line_id='14',
        vehicle_direction='IB',
        vehicle_longitude=-122.41909,
        vehicle_latitude=37.7592278,
        vehicle_bearing=345.0
    )

    stop_monitoring_onward_call = OnwardCall(
        operator_id='SF',
        vehicle_journey_ref='Schedule_0-Est_0',
        dataframe_ref_date=transit_notification.db_commands.parse_time_str('2023-09-26').date(),
        stop_id='15553',
        vehicle_at_stop=True,
        aimed_arrival_time_utc=transit_notification.db_commands.parse_time_str('2023-09-26T15:00:00Z'),
        expected_arrival_time_utc=transit_notification.db_commands.parse_time_str('2023-09-26T15:00:00Z'),
        aimed_departure_time_utc=transit_notification.db_commands.parse_time_str('2023-09-26T15:00:00Z'),
        expected_departure_time_utc=transit_notification.db_commands.parse_time_str(None)
    )

    stop_monitoring_upcoming_vehicles = {
        '14': [transit_notification.db_commands.format_eta_time(dt.timedelta(minutes=0))],
        '49': [transit_notification.db_commands.format_eta_time(dt.timedelta(minutes=4)),
               transit_notification.db_commands.format_eta_time(dt.timedelta(minutes=13)),
               transit_notification.db_commands.format_eta_time(dt.timedelta(minutes=16)),
               transit_notification.db_commands.format_eta_time(dt.timedelta(minutes=40))
               ]
    }

    route_shape = {'line_id': 14,
                  'operator_id': 'SF',
                  'shape_latitude': 37.706479,
                  'shape_longitude': -122.459906,
                  'shape_order': 0}
