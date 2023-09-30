import datetime as dt
from transit_notification.models import Operators, Vehicles, OnwardCalls, Lines, Stops, StopPatterns, Patterns, StopTimetable
import transit_notification.db_commands


class TestComparisonJsons:
    operator_sf = Operators(
        operator_id="SF",
        operator_name="San Francisco Municipal Transportation Agency",
        operator_monitored=True,
        lines_updated=None,
        stops_updated=None,
        stop_monitoring_updated=None,
        vehicle_monitoring_updated=None
    )


    line_14 = Lines(line_id='14', operator_id='SF', line_name="MISSION", line_monitored=True, sort_index=0)
    line_49 = Lines(line_id='49', operator_id='SF', line_name="VAN NESS-MISSION", line_monitored=True, sort_index=1)

    stop_15551 = Stops(operator_id='SF', stop_id='15551', stop_latitude=37.765125, stop_longitude=-122.419668,
                       stop_name='Mission St & 16th St')
    stop_15829 = Stops(operator_id='SF', stop_id='15553', stop_latitude=37.762635, stop_longitude=-122.419348,
                       stop_name="Mission St & 18th St")

    vehicle_0 = Vehicles(
        dataframe_ref_utc=dt.date(2023, 9, 26),
        line_id='14',
        operator_id='SF',
        vehicle_direction='IB',
        vehicle_journey_ref='Schedule_0-Est_0',
        vehicle_latitude=37.7149849,
        vehicle_longitude=-122.442146,
        vehicle_bearing=30.0
    )

    vehicle_1 = Vehicles(
        dataframe_ref_utc=dt.date(2023, 9, 26),
        line_id='14',
        operator_id='SF',
        vehicle_direction='IB',
        vehicle_journey_ref='Schedule_10-Est_13',
        vehicle_latitude=37.7149849,
        vehicle_longitude=-122.442146,
        vehicle_bearing=30.0
    )

    vehicle_2 = Vehicles(
        dataframe_ref_utc=dt.date(2023, 9, 26),
        line_id='14',
        operator_id='SF',
        vehicle_direction='IB',
        vehicle_journey_ref='Schedule_20-Est_16',
        vehicle_latitude=37.7149849,
        vehicle_longitude=-122.442146,
        vehicle_bearing=30.0
    )

    vehicle_onward_calls = [
        OnwardCalls(
                operator_id='SF',
                vehicle_journey_ref='Schedule_0-Est_0',
                dataframe_ref_utc=transit_notification.db_commands.parse_time_str('2023-09-26').date(),
                stop_id='15553',
                vehicle_at_stop=True,
                aimed_arrival_time_utc=transit_notification.db_commands.parse_time_str('2023-09-26T15:00:00Z'),
                expected_arrival_time_utc=transit_notification.db_commands.parse_time_str('2023-09-26T15:00:00Z'),
                aimed_departure_time_utc=transit_notification.db_commands.parse_time_str('2023-09-26T15:00:00Z'),
                expected_departure_time_utc=transit_notification.db_commands.parse_time_str(None)
        ),
        OnwardCalls(
            operator_id='SF',
            vehicle_journey_ref='Schedule_0-Est_0',
            dataframe_ref_utc=transit_notification.db_commands.parse_time_str('2023-09-26').date(),
            stop_id='15551',
            vehicle_at_stop=False,
            aimed_arrival_time_utc=transit_notification.db_commands.parse_time_str("2023-09-26T15:01:28Z"),
            expected_arrival_time_utc=transit_notification.db_commands.parse_time_str("2023-09-26T15:01:17Z"),
            aimed_departure_time_utc=transit_notification.db_commands.parse_time_str("2023-09-26T15:01:28Z"),
            expected_departure_time_utc=transit_notification.db_commands.parse_time_str(None)
        )
    ]

    stop_pattern_1 = StopPatterns(
        operator_id='SF',
        pattern_id=219280,
        stop_order=1,
        stop_id="15568",
        timing_point=True
    )

    pattern_1 = Patterns(
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
