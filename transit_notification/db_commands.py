import pandas as pd
import datetime as dt
import configparser
import numpy as np
import sqlalchemy
from natsort import index_natsorted, natsorted
import os
from itertools import chain
import dateutil
import dateutil.parser
import flask_sqlalchemy
import typing
from collections import defaultdict, OrderedDict

from transit_notification.models import (Operators, Lines, Stops, Vehicles, Patterns, StopPatterns, OnwardCalls,
                                         StopTimetable)
import siri_transit_api_client


def get_operators_dict(transit_api_key: str, siri_base_url: str) -> dict:
    """
    Get operators from SIRI using api key and url

    :param transit_api_key: api key
    :type transit_api_key: api key

    :param siri_base_url: url for the transit api
    :type siri_base_url: url for the transit api

    :return: dictionary containing the operators
    :rtype: dict
    """

    siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
    return siri_client.operators()


def save_operators(siri_db: flask_sqlalchemy.SQLAlchemy, operators_dict: dict) -> None:
    """
    Stores the operators into the database.

    :param siri_db: database
    :type siri_db: flask_sqlalchemy.SQLAlchemy

    :param operators_dict: dictionary that contains the operators
    :type operators_dict: dict

    :return: None
    :rtype: None
    """
    operators_df = pd.DataFrame(operators_dict)
    operators = [Operators(operator_id=row['Id'], operator_name=row['Name'], operator_monitored=row['Monitored'])
                 for _, row in operators_df.iterrows()]
    siri_db.session.add_all(operators)
    siri_db.session.commit()
    return None


def get_lines_dict(transit_api_key, siri_base_url, operator_id) -> dict:
    """
    Get lines from SIRI using api key and url

    :param transit_api_key: api key
    :type transit_api_key: api key

    :param siri_base_url: url for the transit api
    :type siri_base_url: url for the transit api

    :param operator_id: operator id
    :type operator_id: str

    :return: dictionary containing the lines
    :rtype: dict
    """
    siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
    return siri_client.lines(operator_id=operator_id)


def save_lines(siri_db: flask_sqlalchemy.SQLAlchemy, operator_id: str, lines_dict: dict,
               current_time: dt.datetime) -> None:
    """
    Stores the lines into the database.

    :param siri_db: database
    :type siri_db: flask_sqlalchemy.SQLAlchemy

    :param operator_id: operator id
    :type operator_id: str

    :param lines_dict: dictionary that contains the lines
    :type lines_dict: dict

    :param current_time: current utc time
    :type current_time: dt.datetime

    :return: None
    :rtype: None
    """
    lines_df = pd.DataFrame(lines_dict)
    lines_df.sort_values(by="Id",
                         key=lambda x: np.argsort(index_natsorted(lines_df["Id"])),
                         inplace=True,
                         ignore_index=True
                         )
    lines_to_add = [Lines(line_id=row['Id'],
                          operator_id=row['OperatorRef'],
                          line_name=row['Name'],
                          line_monitored=row['Monitored'],
                          sort_index=int(ind))
                    for ind, row in lines_df.iterrows()]

    lines_to_delete = sqlalchemy.delete(Lines).where(Lines.operator_id == operator_id)
    siri_db.session.execute(lines_to_delete)
    siri_db.session.commit()
    siri_db.session.add_all(lines_to_add)
    siri_db.session.commit()
    stmt = sqlalchemy.update(Operators).where(Operators.operator_id == operator_id).values(lines_updated=current_time)
    siri_db.session.execute(stmt)
    siri_db.session.commit()


def get_stops_dict(transit_api_key, siri_base_url, operator_id) -> dict:
    """
    Get stops from SIRI using api key and url

    :param transit_api_key: api key
    :type transit_api_key: api key

    :param siri_base_url: url for the transit api
    :type siri_base_url: url for the transit api

    :param operator_id: operator id
    :type operator_id: str

    :return: dictionary containing the lines
    :rtype: dict
    """

    siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
    return siri_client.stops(operator_id=operator_id)


def save_stops(siri_db: flask_sqlalchemy.SQLAlchemy, operator_id: str, stops_dict: dict,
               current_time: dt.datetime) -> None:
    """
    Stores the lines into the database.

    :param siri_db: database
    :type siri_db: flask_sqlalchemy.SQLAlchemy

    :param operator_id: operator id
    :type operator_id: str

    :param stops_dict: dictionary that contains the stops
    :type stops_dict: dict

    :param current_time: current utc time
    :type current_time: dt.datetime

    :return: None
    :rtype: None
    """

    stop_list = stops_dict['Contents']['dataObjects']['ScheduledStopPoint']
    stops_to_add = [Stops(operator_id=operator_id,
                          stop_id=stop["id"],
                          stop_name=stop['Name'],
                          stop_longitude=float(stop["Location"]["Longitude"]),
                          stop_latitude=float(stop["Location"]["Latitude"]))
                    for stop in stop_list]

    stops_to_delete = sqlalchemy.delete(Stops).where(Stops.operator_id == operator_id)
    siri_db.session.execute(stops_to_delete)
    siri_db.session.commit()
    siri_db.session.add_all(stops_to_add)
    siri_db.session.commit()
    stmt = sqlalchemy.update(Operators).where(Operators.operator_id == operator_id).values(stops_updated=current_time)
    siri_db.session.execute(stmt)
    siri_db.session.commit()


def get_vehicle_monitoring_dict(transit_api_key, siri_base_url, operator_id):
    """
    Get vehicle monitoring from SIRI using api key and url

    :param transit_api_key: api key
    :type transit_api_key: api key

    :param siri_base_url: url for the transit api
    :type siri_base_url: url for the transit api

    :param operator_id: operator id
    :type operator_id: str

    :return: dictionary containing the lines
    :rtype: dict
    """
    siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
    return siri_client.vehicle_monitoring(agency=operator_id)


def save_vehicle_monitoring(siri_db, operator_id: str, vehicle_monitoring: dict,
                            current_time: dt.datetime) -> None:
    """
    Stores the vehicles and vehicle monitoring into the database.

    :param siri_db: database
    :type siri_db: flask_sqlalchemy.SQLAlchemy

    :param operator_id: operator id
    :type operator_id: str

    :param vehicle_monitoring: dictionary that contains the stops
    :type vehicle_monitoring: dict

    :param current_time: current utc time
    :type current_time: dt.datetime

    :return: None
    :rtype: None
    """
    vehicle_list = vehicle_monitoring["Siri"]["ServiceDelivery"]["VehicleMonitoringDelivery"]["VehicleActivity"]
    vehicles_to_add = []
    onward_calls_to_add = []
    for vehicle in vehicle_list:
        vehicle, onward_calls = parse_vehicle_dict(operator_id, vehicle)
        if not vehicle.contains_none():
            vehicles_to_add.append(vehicle)
        if onward_calls:
            onward_calls_to_add.append(onward_calls)

    onward_calls_to_add = list(chain.from_iterable(onward_calls_to_add))

    vehicles_to_delete = sqlalchemy.delete(Vehicles).where(Vehicles.operator_id == operator_id)
    siri_db.session.execute(vehicles_to_delete)
    siri_db.session.commit()
    siri_db.session.add_all(vehicles_to_add)
    siri_db.session.commit()

    onward_calls_to_delete = sqlalchemy.delete(OnwardCalls).where(OnwardCalls.operator_id == operator_id)
    siri_db.session.execute(onward_calls_to_delete)
    siri_db.session.commit()
    siri_db.session.add_all(onward_calls_to_add)
    siri_db.session.commit()

    stmt = sqlalchemy.update(Operators).where(Operators.operator_id == operator_id).values(vehicle_monitoring_updated=current_time)
    siri_db.session.execute(stmt)
    siri_db.session.commit()

    return None


def parse_vehicle_dict(operator_id: str, vehicle_dict: dict) -> (Vehicles, list[OnwardCalls]):
    """
    Parses the vehicle dictionary and returns Vehicles object and a list of onward calls

    :param operator_id: operator id
    :type operator_id: str

    :param vehicle_dict: dictionary for a vehicle to be parsed
    :type vehicle_dict: dict

    :return: returns Vehicles object and a list of onward calls
    :rtype: (Vehicles, list[OnwardCalls])

    """

    dataframe_ref = vehicle_dict["MonitoredVehicleJourney"]["FramedVehicleJourneyRef"]["DataFrameRef"]
    vehicle_journey_ref = vehicle_dict["MonitoredVehicleJourney"]["FramedVehicleJourneyRef"][
        "DatedVehicleJourneyRef"]
    vehicle = Vehicles(operator_id=operator_id,
                       vehicle_journey_ref=vehicle_journey_ref,
                       dataframe_ref_utc=parse_time_str(dataframe_ref).date(),
                       line_id=vehicle_dict["MonitoredVehicleJourney"]["LineRef"],
                       vehicle_direction=vehicle_dict["MonitoredVehicleJourney"]["DirectionRef"],
                       vehicle_longitude=float(vehicle_dict["MonitoredVehicleJourney"]["VehicleLocation"]["Longitude"]),
                       vehicle_latitude=float(vehicle_dict["MonitoredVehicleJourney"]["VehicleLocation"]["Latitude"]),
                       vehicle_bearing=float(vehicle_dict["MonitoredVehicleJourney"]["Bearing"]))

    onward_calls = parse_vehicle_calls(operator_id, vehicle_journey_ref, dataframe_ref,
                                       vehicle_dict["MonitoredVehicleJourney"])

    return vehicle, onward_calls


def parse_vehicle_calls(operator_id: str,
                        vehicle_journey_ref: str,
                        dataframe_ref: str,
                        vehicle_dict: dict) -> list[OnwardCalls]:
    """
    Parses the monitored and onward calls for a vehicle. Returns a list of OnwardCalls Objects.

    :param operator_id: operator id
    :type operator_id: str

    :param vehicle_journey_ref: vehicle journey ref
    :type vehicle_journey_ref: str

    :param dataframe_ref: date for the vehicle journey. Combination of operator id, vehicle journey ref and date
        is a unique identifier.
    :type dataframe_ref: str

    :param vehicle_dict: dictionary for a vehicle to be parsed
    :type vehicle_dict: dict

    :return: list containing parsed monitored and onward calls
    :rtype: list[OnwardCalls]
    """
    ret_list = []
    if "OnwardCalls" in vehicle_dict:
        ret_list = [OnwardCalls(operator_id=operator_id,
                                vehicle_journey_ref=vehicle_journey_ref,
                                dataframe_ref_utc=parse_time_str(dataframe_ref).date(),
                                stop_id=call_json["StopPointRef"],
                                vehicle_at_stop=False,
                                aimed_arrival_time_utc=parse_time_str(call_json["AimedArrivalTime"]),
                                expected_arrival_time_utc=parse_time_str(call_json["ExpectedArrivalTime"]),
                                aimed_departure_time_utc=parse_time_str(call_json["AimedDepartureTime"]),
                                expected_departure_time_utc=parse_time_str(call_json["ExpectedDepartureTime"]))
                    for call_json in vehicle_dict["OnwardCalls"]["OnwardCall"]]

    if "MonitoredCall" in vehicle_dict:
        monitored_call = OnwardCalls(operator_id=operator_id,
                                     vehicle_journey_ref=vehicle_journey_ref,
                                     dataframe_ref_utc=parse_time_str(dataframe_ref).date(),
                                     stop_id=vehicle_dict["MonitoredCall"]["StopPointRef"],
                                     vehicle_at_stop=bool(vehicle_dict["MonitoredCall"]["VehicleAtStop"]),
                                     aimed_arrival_time_utc=parse_time_str(vehicle_dict["MonitoredCall"][
                                                                               "AimedArrivalTime"]),
                                     expected_arrival_time_utc=parse_time_str(vehicle_dict["MonitoredCall"][
                                                                                  "ExpectedArrivalTime"]),
                                     aimed_departure_time_utc=parse_time_str(vehicle_dict["MonitoredCall"][
                                                                                 "AimedDepartureTime"]),
                                     expected_departure_time_utc=parse_time_str(vehicle_dict["MonitoredCall"][
                                                                                    "ExpectedDepartureTime"]))
        ret_list.append(monitored_call)

    return ret_list


def get_pattern_dict(transit_api_key: str, siri_base_url: str, operator_id: str, line_id: str) -> dict:
    """
    Get patterns from SIRI using api key and url

    :param transit_api_key: api key
    :type transit_api_key: api key

    :param siri_base_url: url for the transit api
    :type siri_base_url: url for the transit api

    :param operator_id: operator id
    :type operator_id: str

    :param line_id: line id
    :type line_id: str

    :return: dictionary containing the lines
    :rtype: dict
    """
    siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
    return siri_client.patterns(operator_id=operator_id, line_id=line_id)


def save_patterns(siri_db: flask_sqlalchemy.SQLAlchemy, operator_id: str, line_id: str, pattern_dict: dict) -> None:
    """
    Save the patterns into the database. Adds direction to lines.

    :param siri_db: database
    :type siri_db: flask_sqlalchemy.SQLAlchemy

    :param operator_id: operator id
    :type operator_id: str

    :param line_id: line id
    :type line_id: str

    :param pattern_dict: dictionary that contains the pattern
    :type pattern_dict: dict

    :return: None
    :rtype: None

    """
    directions = pattern_dict["directions"]
    stmt = sqlalchemy.update(Lines).where(Lines.operator_id == operator_id,
                                          Lines.line_id == line_id).values(
        {
           "direction_0_id": directions[0]["DirectionId"],
            "direction_0_name": directions[0]["Name"],
            "direction_1_id": directions[1]["DirectionId"],
            "direction_1_name": directions[1]["Name"]
        })
    siri_db.session.execute(stmt)
    siri_db.session.commit()

    patterns_to_add = []
    for pattern in pattern_dict['journeyPatterns']:
        patterns_to_add.append(Patterns(operator_id=operator_id,
                                 line_id=pattern['LineRef'],
                                 pattern_id=pattern['serviceJourneyPatternRef'],
                                 pattern_name=pattern['Name'],
                                 pattern_direction=pattern['DirectionRef'],
                                 pattern_trip_count=pattern['TripCount']))
        save_stop_pattern(siri_db, operator_id, pattern['serviceJourneyPatternRef'], pattern['PointsInSequence'])

    patterns_to_delete = sqlalchemy.delete(Patterns).where(Patterns.operator_id == operator_id,
                                                           Patterns.line_id == line_id)
    siri_db.session.execute(patterns_to_delete)
    siri_db.session.commit()

    siri_db.session.add_all(patterns_to_add)
    siri_db.session.commit()
    return None


def save_stop_pattern(siri_db: flask_sqlalchemy.SQLAlchemy, operator_id: str, pattern_id: str, stop_pattern_dict: dict) -> None:
    """
    Save the patterns into the database. Adds direction to lines.

    :param siri_db: database
    :type siri_db: flask_sqlalchemy.SQLAlchemy

    :param operator_id: operator id
    :type operator_id: str

    :param pattern_id: pattern id
    :type pattern_id: str

    :param stop_pattern_dict: dictionary that contains the stop pattern
    :type stop_pattern_dict: dict

    :return: None
    :rtype: None
    """

    untimed_stops = [StopPatterns(operator_id=operator_id,
                                  pattern_id=pattern_id,
                                  stop_order=stop_pattern["Order"],
                                  stop_id=stop_pattern["ScheduledStopPointRef"],
                                  timing_point=False)
                     for stop_pattern in stop_pattern_dict['StopPointInJourneyPattern']]
    timed_stops = [StopPatterns(operator_id=operator_id,
                                pattern_id=pattern_id,
                                stop_order=stop_pattern["Order"],
                                stop_id=stop_pattern["ScheduledStopPointRef"],
                                timing_point=True)
                   for stop_pattern in stop_pattern_dict['TimingPointInJourneyPattern']]

    stop_patterns_to_delete = sqlalchemy.delete(StopPatterns).where(StopPatterns.operator_id == operator_id,
                                                                StopPatterns.pattern_id == pattern_id)
    siri_db.session.execute(stop_patterns_to_delete)
    siri_db.session.commit()

    siri_db.session.add_all(untimed_stops + timed_stops)
    siri_db.session.commit()
    return None


def upcoming_vehicles_vm(siri_db: flask_sqlalchemy.SQLAlchemy, operator_id: str, stop_id: str,
                         current_time: dt.datetime) -> dict:
    """
    Creates a list containing information for upcoming vehicles to a stop.

    :param siri_db: database
    :type siri_db: flask_sqlalchemy.SQLAlchemy

    :param operator_id: operator id
    :type operator_id: str

    :param stop_id: stop id
    :type stop_id: str

    :param current_time: current utc time
    :type current_time: dt.datetime

    :return: list containing upcoming vehicles to a stop
    :rtype: list[dict]
    """

    stmt = siri_db.select(Vehicles, OnwardCalls).join(OnwardCalls).filter(OnwardCalls.stop_id == stop_id)
    response_dict = defaultdict(list)
    for row in siri_db.session.execute(stmt):
        vehicle = row[0]
        onward_call = row[1]
        vehicle_at_stop = onward_call.vehicle_at_stop
        if vehicle_at_stop:
            eta_time = dt.timedelta(seconds=0)
        else:
            expected_arrival_time_utc = onward_call.expected_arrival_time_utc
            eta_time = expected_arrival_time_utc.replace(tzinfo=dt.timezone.utc) - current_time
        if eta_time >= dt.timedelta(seconds=0):
            response_dict[vehicle.line_id].append(format_eta_time(eta_time))

    return response_dict


def stop_timetable(siri_db: flask_sqlalchemy.SQLAlchemy, operator_id: str, stop_id: str, timetable_dict: dict) -> None:
    """
   Store timetable for a given stop in the database.

   :param siri_db: database
   :type siri_db: flask_sqlalchemy.SQLAlchemy

   :param operator_id: operator id
   :type operator_id: str

   :param stop_id: stop id
   :type stop_id: str

   :param timetable_dict: dictionary containing timetable for a given stop
   :type timetable_dict: dict

   :return: none
   :rtype: None
   """
    timetable_list = timetable_dict["Siri"]["ServiceDelivery"]["StopTimetableDelivery"]["TimetabledStopVisit"]
    stop_timetable_list = [StopTimetable(operator_id=operator_id,
                                    vehicle_journey_ref=timetable["TargetedVehicleJourney"]["DatedVehicleJourneyRef"],
                                    stop_id=timetable["MonitoringRef"],
                                    aimed_arrival_time_utc=parse_time_str(timetable["TargetedVehicleJourney"]["TargetedCall"]["AimedArrivalTime"]),
                                    aimed_departure_time_utc=parse_time_str(timetable["TargetedVehicleJourney"]["TargetedCall"]["AimedDepartureTime"])
                                    )
                      for timetable in timetable_list]

    stop_timetable_to_delete = sqlalchemy.delete(StopTimetable).where(StopTimetable.operator_id == operator_id,
                                                                StopTimetable.stop_id == stop_id)
    siri_db.session.execute(stop_timetable_to_delete)
    siri_db.session.commit()

    siri_db.session.add_all(stop_timetable_list)
    siri_db.session.commit()
    return None


def write_key_api_file(input_dict: dict) -> None:
    """
    Writes the key and url to the key_api_file

    :param input_dict: dict containing the key and url
    :type input_dict: dict

    :return: None
    """
    # Add content to the file
    config = configparser.ConfigParser()
    for key in input_dict:
        config[key] = input_dict[key]
    with open(key_api_filename(), 'w') as configfile:
        config.write(configfile)
    return None


def read_key_api_file() -> (str, str):
    """
    Reads the key and url form the key_api_file

    :return: tuple containing key and url
    :rtype: tuple(str, str)
    """
    config = configparser.ConfigParser()
    config.read(key_api_filename())
    return config["SIRI"]["api_key"], config["SIRI"]["base_url"]


def key_api_filename() -> str:
    """
    Returns the key api filename from the environmental variables
    """
    return os.environ.get("KEY_API_FILE", "dev")


def refresh_needed(siri_db: flask_sqlalchemy.SQLAlchemy,
                   operator_id: str,
                   table_name: str,
                   refresh_limit: float) -> bool:
    """
    Determines if refresh of a given table is needed.

    :param operator_id: ID for the operator
    :type operator_id: str

    :param table_name: name of the table to be checked
    :type table_name: str

    :param refresh_limit: minimum time to elapse before refreshing table
    :type refresh_limit: float

    :return: boolean for if the table should be refreshed
    :rtype: bool
    """
    operator = siri_db.session.execute(siri_db.select(Operators).filter_by(operator_id=operator_id)).scalar_one()
    current_time = dt.datetime.utcnow()
    last_update_time = operator.__dict__[table_name]
    if last_update_time is None:
        return True
    delta_time = current_time - last_update_time
    return delta_time >= dt.timedelta(hours=refresh_limit)


def parse_time_str(time_str: typing.Optional[str] = None):
    """
    Parses the time string and returns datetime object if time string is not none. If none, returns none.

    """
    if time_str is None:
        return None
    else:
        dt_obj = dateutil.parser.isoparse(time_str)
        if dt_is_timezone_aware(dt_obj):
            return dt_obj.astimezone(dateutil.tz.UTC).replace(tzinfo=None)
        else:
            return dt_obj


def dt_is_timezone_aware(dt_obj):
    # Checks if a given datetime object is timezone aware.
    # Returns True if the datetime object is timezone aware, False otherwise.
    return dt_obj.tzinfo is not None and dt_obj.tzinfo.utcoffset(dt_obj) is not None


def format_eta_time(time_delta: dt.timedelta) -> str:
    """
    Formats the timedelta object to a string that represents eta of buses

    :param time_delta: timedelta object that represents difference between eta and current time
    :type time_delta: dt.timedelta

    :return: str to represent eta
    :rtype: str

    """
    minutes = (time_delta.total_seconds()) // 60
    if minutes == 0:
        return "Arriving"
    elif minutes == 1:
        return "{:.0f} min".format(minutes)
    else:
        return "{:.0f} mins".format(minutes)


def sort_response_dict(input_dict):
    sorted_dict = OrderedDict(sorted(input_dict.items()))
    for key in sorted_dict:
        eta_list = sorted_dict[key]
        if 'Arriving' in eta_list:
            eta_list.remove('Arriving')
            eta_list = natsorted(eta_list)
            eta_list.insert(0, 'Arriving')
        else:
            eta_list = natsorted(eta_list)
        len_list = len(eta_list)
        ret_str = ''
        for count, value in enumerate(eta_list):
            ret_str += value
            if count < len_list - 1:
                ret_str += ', '
        sorted_dict[key] = ret_str
    return sorted_dict
