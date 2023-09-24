import datetime as dt
from transit_notification.models import Operators, Vehicles, OnwardCalls, Lines, Stops, StopPatterns, Patterns, StopTimetable
import transit_notification.db_commands


class TestComparisonJsons:
    operator_sf = Operators(
        operator_id="SF",
        lines_updated=None,
        stops_updated=None,
        operator_monitored=True,
        operator_name="San Francisco Municipal Transportation Agency",
        vehicle_monitoring_updated=None
    )

    line_f = Lines(line_id='F', operator_id='SF', line_name="MARKET \u0026 WHARVES", line_monitored=True, sort_index=1)
    line_14 = Lines(line_id='14', operator_id='SF', line_name="MISSION", line_monitored=True, sort_index=0)

    stop_13230 = Stops(operator_id='SF', stop_id='13230', stop_latitude=37.752724, stop_longitude=-122.466502,
                       stop_name='10th Ave & Ortega St')
    stop_15829 = Stops(operator_id='SF', stop_id='15829', stop_latitude=37.744481, stop_longitude=-122.450678,
                       stop_name="100 O'Shaughnessy Blvd")

    vehicle_0 = Vehicles(
        dataframe_ref_utc=dt.date(2023, 9, 21),
        line_id='49',
        operator_id='SF',
        vehicle_direction='IB',
        vehicle_journey_ref='Schedule_0-Est_0',
        vehicle_latitude=37.7238045,
        vehicle_longitude=-122.452667,
        vehicle_bearing=90
    )

    vehicle_1 = Vehicles(
        dataframe_ref_utc=dt.date(2023, 9, 21),
        line_id='49',
        operator_id='SF',
        vehicle_direction='IB',
        vehicle_journey_ref='Schedule_10-Est_13',
        vehicle_latitude=37.7238045,
        vehicle_longitude=-122.452667,
        vehicle_bearing=90
    )

    vehicle_2 = Vehicles(
        dataframe_ref_utc=dt.date(2023, 9, 21),
        line_id='49',
        operator_id='SF',
        vehicle_direction='IB',
        vehicle_journey_ref='Schedule_20-Est_16',
        vehicle_latitude=37.7238045,
        vehicle_longitude=-122.452667,
        vehicle_bearing=90
    )

    vehicle_onward_calls = [
        OnwardCalls(
                operator_id='SF',
                vehicle_journey_ref='Schedule_0-Est_0',
                dataframe_ref_utc=transit_notification.db_commands.parse_time_str('2023-09-21').date(),
                stop_id='15551',
                vehicle_at_stop=False,
                aimed_arrival_time_utc=transit_notification.db_commands.parse_time_str('2023-09-21T14:01:57Z'),
                expected_arrival_time_utc=transit_notification.db_commands.parse_time_str('2023-09-21T14:02:01Z'),
                aimed_departure_time_utc=transit_notification.db_commands.parse_time_str('2023-09-21T14:01:57Z'),
                expected_departure_time_utc=transit_notification.db_commands.parse_time_str(None)
        ),
        OnwardCalls(
            operator_id='SF',
            vehicle_journey_ref='Schedule_0-Est_0',
            dataframe_ref_utc=transit_notification.db_commands.parse_time_str('2023-09-21').date(),
            stop_id='15553',
            vehicle_at_stop=True,
            aimed_arrival_time_utc=transit_notification.db_commands.parse_time_str("2023-09-21T14:00:29Z"),
            expected_arrival_time_utc=transit_notification.db_commands.parse_time_str("2023-09-21T14:00:29Z"),
            aimed_departure_time_utc=transit_notification.db_commands.parse_time_str("2023-09-21T14:00:29Z"),
            expected_departure_time_utc=transit_notification.db_commands.parse_time_str(None)
        )
    ]

    stop_pattern_1 = StopPatterns(
        operator_id='SF',
        pattern_id=219278,
        stop_order=1,
        stop_id="16498",
        timing_point=True
    )

    pattern_1 = Patterns(
        operator_id='SF',
        line_id='14',
        pattern_id=219278,
        pattern_name='Mission St & San Jose Ave',
        pattern_direction='OB',
        pattern_trip_count=1104
    )

    stop_timetable_1 = StopTimetable(
        operator_id='SF',
        vehicle_journey_ref='Schedule_0-Est_0',
        stop_id='15553',
        aimed_arrival_time_utc=dt.datetime(2023, 9, 21, 14, 0, 29),
        aimed_departure_time_utc=dt.datetime(2023, 9, 21, 14, 0, 29)
    )

    upcoming_vehicles = {
        "49": [transit_notification.db_commands.format_eta_time(dt.timedelta(minutes=0)),
               transit_notification.db_commands.format_eta_time(dt.timedelta(minutes=13)),
               transit_notification.db_commands.format_eta_time(dt.timedelta(minutes=16))
               ]
    }
