import pandas as pd
import datetime as dt
from transit_notification.models import Operators, Lines, Stops, Vehicles, Patterns, StopPatterns
import siri_transit_api_client
import configparser
import numpy as np
from natsort import index_natsorted

config_filename = "config.ini"


def commit_operators(siri_db, transit_api_key, siri_base_url):
    siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
    operators_dict = siri_client.operators()
    operators_df = pd.DataFrame(operators_dict)

    operators = [Operators(id=row['Id'], name=row['Name'], monitored=row['Monitored'])
                 for _, row in operators_df.iterrows()]

    siri_db.session.add_all(operators)
    siri_db.session.commit()
    return None


def commit_lines(siri_db, operator_id):
    transit_api_key, siri_base_url = read_configuration_file()
    siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
    lines_dict = siri_client.lines(operator_id=operator_id)
    lines_df = pd.DataFrame(lines_dict)
    lines_df.sort_values(by="Id",
                         key=lambda x: np.argsort(index_natsorted(lines_df["Id"])),
                         inplace=True,
                         ignore_index=True
                         )
    lines = [Lines(id=row['Id'],
                   operator_id=row['OperatorRef'],
                   name=row['Name'],
                   monitored=row['Monitored'],
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
    return None


def commit_stops(siri_db, operator_id):
    transit_api_key, siri_base_url = read_configuration_file()
    siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)

    stops_dict = siri_client.stops(operator_id=operator_id)
    stop_list = stops_dict['Contents']['dataObjects']['ScheduledStopPoint']

    stops = [Stops(operator_id=operator_id,
                   id=stop["id"],
                   name=stop['Name'],
                   longitude=float(stop["Location"]["Longitude"]),
                   latitude=float(stop["Location"]["Latitude"]))
             for stop in stop_list]
    Stops.query.filter_by(operator_id=operator_id).delete()
    siri_db.session.commit()
    siri_db.session.add_all(stops)
    siri_db.session.commit()
    current_time = dt.datetime.utcnow()
    operator = Operators.query.filter_by(id=operator_id).first()
    operator.stops_updated = current_time
    siri_db.session.commit()
    return None


def commit_vehicle_monitoring(siri_db, operator_id):
    transit_api_key, siri_base_url = read_configuration_file()
    siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)

    vehicle_monitoring = siri_client.vehicle_monitoring(agency=operator_id)
    vehicle_list = vehicle_monitoring["Siri"]["ServiceDelivery"]["VehicleMonitoringDelivery"]["VehicleActivity"]

    vehicles = [Vehicles(operator_id=operator_id,
                         vehicle_journey_ref=vehicle["MonitoredVehicleJourney"]["FramedVehicleJourneyRef"]["DatedVehicleJourneyRef"],
                         dataframe_ref=vehicle["MonitoredVehicleJourney"]["FramedVehicleJourneyRef"]["DataFrameRef"],
                         line_id=vehicle["MonitoredVehicleJourney"]["LineRef"],
                         direction=vehicle["MonitoredVehicleJourney"]["DirectionRef"],
                         longitude=float(vehicle["MonitoredVehicleJourney"]["VehicleLocation"]["Longitude"]),
                         latitude=float(vehicle["MonitoredVehicleJourney"]["VehicleLocation"]["Latitude"]))
                for vehicle in vehicle_list]
    Vehicles.query.filter_by(operator_id=operator_id).delete()
    siri_db.session.commit()
    siri_db.session.add_all(vehicles)
    siri_db.session.commit()
    current_time = dt.datetime.utcnow()
    operator = Operators.query.filter_by(id=operator_id).first()
    operator.vehicle_monitoring_updated = current_time
    siri_db.session.commit()
    return None


def commit_pattern(siri_db, operator_id, line_id):
    transit_api_key, siri_base_url = read_configuration_file()
    siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
    pattern_json = siri_client.patterns(operator_id=operator_id, line_id=line_id)
    directions = pattern_json["directions"]
    line = Lines.query.where(siri_db.and_(Lines.operator_id == operator_id, Lines.id == line_id)).first()
    line.direction_0_id = directions[0]["DirectionId"]
    line.direction_0_name = directions[0]["Name"]
    line.direction_1_id = directions[1]["DirectionId"]
    line.direction_1_name = directions[1]["Name"]
    siri_db.session.commit()
    patterns = [Patterns(operator_id=operator_id,
                         line_id=pattern['LineRef'],
                         id=pattern['serviceJourneyPatternRef'],
                         name=pattern['Name'],
                         direction=pattern['DirectionRef'],
                         trip_count=pattern['TripCount'])
                for pattern in pattern_json['journeyPatterns']]
    Patterns.query.filter(siri_db.and_(Patterns.operator_id == operator_id, Patterns.line_id == line_id)).delete()
    siri_db.session.commit()
    siri_db.session.add_all(patterns)
    siri_db.session.commit()
    return None


def get_dropdown_values():
    """
    dummy function, replace with e.g. database call. If data not change, this function is not needed but dictionary
could be defined globally
    """

    # Create a dictionary (myDict) where the key is
    # the name of the brand, and the list includes the names of the car models
    #
    # Read from the database the list of cars and the list of models.
    # With this information, build a dictionary that includes the list of models by brand.
    # This dictionary is used to feed the drop-down boxes of car brands and car models that belong to a car brand.

    operators = Operators.query.all()
    # Create an empty dictionary
    operator_dict = {}
    for operator in operators:

        name = operator.name
        operator_id = operator.id

        """
        # Select all car models that belong to a car brand
        q = Carmodels.query.filter_by(brand_id=brand_id).all()

        # build the structure (lst_c) that includes the names of the car models that belong to the car brand
        lst_c = []
        for c in q:
            lst_c.append(c.car_model)
        """
        operator_dict[name] = operator_id #lst_c

    return operator_dict


def write_configuration_file(input_dict):
    # Add content to the file
    config = configparser.ConfigParser()
    for key in input_dict:
        config[key] = input_dict[key]
    with open(config_filename, 'w') as configfile:
        config.write(configfile)


def read_configuration_file():
    config = configparser.ConfigParser()
    config.read(config_filename)
    return config["SIRI"]["api_key"], config["SIRI"]["base_url"]
