import pandas as pd
import datetime as dt
from transit_notification.models import Operators, Lines, Stops, Vehicles, Patterns, StopPatterns
import siri_transit_api_client
import configparser
import numpy as np
from natsort import index_natsorted
import os

# units are hours
OPERATORS_REFRESH_LIMIT = 24
LINES_REFRESH_LIMIT = 24
STOPS_REFRESH_LIMIT = 24
PATTERN_REFRESH_LIMIT = 24
VEHICLE_MONITORING_REFRESH_LIMIT = 24


def commit_operators(siri_db, transit_api_key, siri_base_url):
    siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
    operators_dict = siri_client.operators()
    save_operators(siri_db, operators_dict)
    return None


def save_operators(siri_db, operators_dict):
    operators_df = pd.DataFrame(operators_dict)
    operators = [Operators(operator_id=row['Id'], operator_name=row['Name'], operator_monitored=row['Monitored'])
                 for _, row in operators_df.iterrows()]
    siri_db.session.add_all(operators)
    siri_db.session.commit()
    return None


def commit_lines(siri_db, operator_id):
    if refresh_needed(operator_id, 'lines_updated', LINES_REFRESH_LIMIT):
        transit_api_key, siri_base_url = read_key_api_file()
        siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
        lines_dict = siri_client.lines(operator_id=operator_id)
        save_lines(siri_db, operator_id, lines_dict)
    return None


def save_lines(siri_db, operator_id, lines_dict):
    lines_df = pd.DataFrame(lines_dict)
    lines_df.sort_values(by="Id",
                         key=lambda x: np.argsort(index_natsorted(lines_df["Id"])),
                         inplace=True,
                         ignore_index=True
                         )
    lines = [Lines(line_id=row['Id'],
                   operator_id=row['OperatorRef'],
                   line_name=row['Name'],
                   line_monitored=row['Monitored'],
                   sort_index=index)
             for index, row in lines_df.iterrows()]
    Lines.query.filter_by(operator_id=operator_id).delete()
    siri_db.session.commit()
    siri_db.session.add_all(lines)
    siri_db.session.commit()
    current_time = dt.datetime.utcnow()
    operator = Operators.query.filter_by(id=operator_id).first()
    operator.lines_updated = current_time
    siri_db.session.commit()


def commit_stops(siri_db, operator_id):
    if refresh_needed(operator_id, 'stops_updated', STOPS_REFRESH_LIMIT):
        transit_api_key, siri_base_url = read_key_api_file()
        siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
        stops_dict = siri_client.stops(operator_id=operator_id)
        save_stop(siri_db, operator_id, stops_dict)
    return None


def save_stop(siri_db, operator_id, stops_dict):
    stop_list = stops_dict['Contents']['dataObjects']['ScheduledStopPoint']
    stops = [Stops(operator_id=operator_id,
                   stop_id=stop["id"],
                   stop_name=stop['Name'],
                   stop_longitude=float(stop["Location"]["Longitude"]),
                   stop_latitude=float(stop["Location"]["Latitude"]))
             for stop in stop_list]
    Stops.query.filter_by(operator_id=operator_id).delete()
    siri_db.session.commit()
    siri_db.session.add_all(stops)
    siri_db.session.commit()
    current_time = dt.datetime.utcnow()
    operator = Operators.query.filter_by(id=operator_id).first()
    operator.stops_updated = current_time
    siri_db.session.commit()


def commit_vehicle_monitoring(siri_db, operator_id):
    if refresh_needed(operator_id, 'vehicle_monitoring_updated', VEHICLE_MONITORING_REFRESH_LIMIT):
        transit_api_key, siri_base_url = read_key_api_file()
        siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
        vehicle_monitoring = siri_client.vehicle_monitoring(agency=operator_id)
        save_vehicle_monitoring(siri_db, operator_id, vehicle_monitoring)
    return None


def save_vehicle_monitoring(siri_db, operator_id, vehicle_monitoring):
    vehicle_list = vehicle_monitoring["Siri"]["ServiceDelivery"]["VehicleMonitoringDelivery"]["VehicleActivity"]
    all_vehicles = [Vehicles(operator_id=operator_id,
                         vehicle_journey_ref=vehicle["MonitoredVehicleJourney"]["FramedVehicleJourneyRef"][
                             "DatedVehicleJourneyRef"],
                         dataframe_ref=vehicle["MonitoredVehicleJourney"]["FramedVehicleJourneyRef"]["DataFrameRef"],
                         line_id=vehicle["MonitoredVehicleJourney"]["LineRef"],
                         vehicle_direction=vehicle["MonitoredVehicleJourney"]["DirectionRef"],
                         vehicle_longitude=float(vehicle["MonitoredVehicleJourney"]["VehicleLocation"]["Longitude"]),
                         vehicle_latitude=float(vehicle["MonitoredVehicleJourney"]["VehicleLocation"]["Latitude"]))
                for vehicle in vehicle_list]
    vehicles = [vehicle for vehicle in all_vehicles if not vehicle.contains_none()]
    Vehicles.query.filter_by(operator_id=operator_id).delete()
    siri_db.session.commit()
    siri_db.session.add_all(vehicles)
    siri_db.session.commit()
    current_time = dt.datetime.utcnow()
    operator = Operators.query.filter_by(id=operator_id).first()
    operator.vehicle_monitoring_updated = current_time
    siri_db.session.commit()


def save_onward_calls(siri_db, operator_id, vehicle_journey_ref, dataframe_ref, onward_calls_dict):
    pass


def commit_pattern(siri_db, operator_id, line_id):
    transit_api_key, siri_base_url = read_key_api_file()
    siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
    pattern_json = siri_client.patterns(operator_id=operator_id, line_id=line_id)
    directions = pattern_json["directions"]
    line = Lines.query.where(siri_db.and_(Lines.operator_id == operator_id, Lines.line_id == line_id)).first()
    line.direction_0_id = directions[0]["DirectionId"]
    line.direction_0_name = directions[0]["Name"]
    line.direction_1_id = directions[1]["DirectionId"]
    line.direction_1_name = directions[1]["Name"]
    siri_db.session.commit()
    patterns = []
    for pattern in pattern_json['journeyPatterns']:
        patterns.append(Patterns(operator_id=operator_id,
                                 line_id=pattern['LineRef'],
                                 pattern_id=pattern['serviceJourneyPatternRef'],
                                 pattern_name=pattern['Name'],
                                 pattern_direction=pattern['DirectionRef'],
                                 pattern_trip_count=pattern['TripCount']))
        commit_stop_pattern(siri_db, pattern['PointsInSequence']['StopPointInJourneyPattern'], operator_id,
                            pattern['serviceJourneyPatternRef'])
    Patterns.query.filter(siri_db.and_(Patterns.operator_id == operator_id, Patterns.line_id == line_id)).delete()
    siri_db.session.commit()
    siri_db.session.add_all(patterns)
    siri_db.session.commit()
    return None


def commit_stop_pattern(siri_db, stop_pattern_json, operator_id, pattern_id):
    stop_patterns = [StopPatterns(operator_id=operator_id,
                                  pattern_id=pattern_id,
                                  stop_order=stop_pattern["Order"],
                                  stop_id=stop_pattern["ScheduledStopPointRef"])
                     for stop_pattern in stop_pattern_json]
    StopPatterns.query.filter(siri_db.and_(StopPatterns.operator_id == operator_id,
                                           StopPatterns.pattern_id == pattern_id)).delete()
    siri_db.session.commit()
    siri_db.session.add_all(stop_patterns)
    siri_db.session.commit()


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
    :rtype: tuple(str)
    """
    config = configparser.ConfigParser()
    config.read(key_api_filename())
    return config["SIRI"]["api_key"], config["SIRI"]["base_url"]


def key_api_filename():
    config = configparser.ConfigParser()
    config.read(os.environ.get("CONFIG_FILE", "dev"))
    return config["FILE_LOCATIONS"]["KEY_API"]


def refresh_needed(operator_id: str, table_name: str, refresh_limit: float) -> bool:
    """
    Determines if refresh of a given table is needed.

    :param operator_id: ID for the operator
    :type operator_id: str

    :param table_name: name of the table to be checked
    :type table_name: str

    :param refresh_limit: minimum time to elapse before refreshing table
    :type refresh_limit: float

    :return: should the table refreshed
    :rtype: bool
    """
    operator = Operators.query.filter_by(id=operator_id).first()
    current_time = dt.datetime.utcnow()
    last_update_time = operator.__dict__[table_name]
    if last_update_time is None:
        last_update_time = current_time - dt.timedelta(hours=refresh_limit)
    delta_time = current_time - last_update_time
    return delta_time >= dt.timedelta(hours=refresh_limit)
