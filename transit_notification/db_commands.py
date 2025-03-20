import pandas as pd
import datetime as dt
import numpy as np
from natsort import index_natsorted, natsorted
import os
from itertools import chain
import dateutil
import dateutil.parser
import flask_sqlalchemy
import typing
from collections import defaultdict, OrderedDict
from sqlalchemy import func

from transit_notification.models import (Operator, Line, Stop, Vehicle, Pattern, StopPattern, OnwardCall,
                                         StopTimetable, Parameter, Shape)
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
    operators = [Operator(operator_id=row['Id'], operator_name=row['Name'], operator_monitored=row['Monitored'])
                 for _, row in operators_df.iterrows()]

    operators_to_delete = siri_db.delete(Operator)
    siri_db.session.execute(operators_to_delete)
    siri_db.session.commit()
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
    lines_to_add = [Line(line_id=row['Id'],
                         operator_id=row['OperatorRef'],
                         line_name=row['Name'],
                         line_monitored=row['Monitored'],
                         sort_index=int(ind))
                    for ind, row in lines_df.iterrows()]

    lines_to_delete = siri_db.delete(Line).where(Line.operator_id == operator_id)
    siri_db.session.execute(lines_to_delete)
    siri_db.session.commit()
    siri_db.session.add_all(lines_to_add)
    siri_db.session.commit()
    stmt = siri_db.update(Operator).where(Operator.operator_id == operator_id).values(lines_updated=current_time)
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
    stops_to_add = [Stop(operator_id=operator_id,
                         stop_id=stop["id"],
                         stop_name=stop['Name'],
                         stop_longitude=float(stop["Location"]["Longitude"]),
                         stop_latitude=float(stop["Location"]["Latitude"]))
                    for stop in stop_list]

    stops_to_delete = siri_db.delete(Stop).where(Stop.operator_id == operator_id)
    siri_db.session.execute(stops_to_delete)
    siri_db.session.commit()
    siri_db.session.add_all(stops_to_add)
    siri_db.session.commit()
    stmt = siri_db.update(Operator).where(Operator.operator_id == operator_id).values(stops_updated=current_time)
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

    vehicles_to_delete = siri_db.delete(Vehicle).where(Vehicle.operator_id == operator_id)
    siri_db.session.execute(vehicles_to_delete)
    siri_db.session.commit()
    siri_db.session.add_all(vehicles_to_add)
    siri_db.session.commit()

    onward_calls_to_delete = siri_db.delete(OnwardCall).where(OnwardCall.operator_id == operator_id)
    siri_db.session.execute(onward_calls_to_delete)
    siri_db.session.commit()
    siri_db.session.add_all(onward_calls_to_add)
    siri_db.session.commit()

    stmt = siri_db.update(Operator).where(Operator.operator_id == operator_id).values(
        vehicle_monitoring_updated=current_time)
    siri_db.session.execute(stmt)
    siri_db.session.commit()

    return None


def parse_vehicle_dict(operator_id: str, vehicle_dict: dict) -> (Vehicle, list[OnwardCall]):
    """
    Parses the vehicle dictionary and returns Vehicle object and a list of onward calls

    :param operator_id: operator id
    :type operator_id: str

    :param vehicle_dict: dictionary for a vehicle to be parsed
    :type vehicle_dict: dict

    :return: returns Vehicle object and a list of onward calls
    :rtype: (Vehicle, list[OnwardCall])

    """

    dataframe_ref = vehicle_dict["MonitoredVehicleJourney"]["FramedVehicleJourneyRef"]["DataFrameRef"]
    vehicle_journey_ref = vehicle_dict["MonitoredVehicleJourney"]["FramedVehicleJourneyRef"][
        "DatedVehicleJourneyRef"]
    vehicle = Vehicle(operator_id=operator_id,
                      vehicle_journey_ref=vehicle_journey_ref,
                      dataframe_ref_date=parse_time_str(dataframe_ref).date(),
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
                        vehicle_dict: dict) -> list[OnwardCall]:
    """
    Parses the monitored and onward calls for a vehicle. Returns a list of OnwardCall Objects.

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
    :rtype: list[OnwardCall]
    """
    ret_list = []
    if "OnwardCalls" in vehicle_dict:
        ret_list = [OnwardCall(operator_id=operator_id,
                               vehicle_journey_ref=vehicle_journey_ref,
                               dataframe_ref_date=parse_time_str(dataframe_ref).date(),
                               stop_id=call_json["StopPointRef"],
                               vehicle_at_stop=False,
                               aimed_arrival_time_utc=parse_time_str(call_json["AimedArrivalTime"]),
                               expected_arrival_time_utc=parse_time_str(call_json["ExpectedArrivalTime"]),
                               aimed_departure_time_utc=parse_time_str(call_json["AimedDepartureTime"]),
                               expected_departure_time_utc=parse_time_str(call_json["ExpectedDepartureTime"]))
                    for call_json in vehicle_dict["OnwardCalls"]["OnwardCall"]]

    if "MonitoredCall" in vehicle_dict:
        monitored_call = OnwardCall(operator_id=operator_id,
                                    vehicle_journey_ref=vehicle_journey_ref,
                                    dataframe_ref_date=parse_time_str(dataframe_ref).date(),
                                    stop_id=vehicle_dict["MonitoredCall"]["StopPointRef"],
                                    vehicle_at_stop=parse_bools(vehicle_dict["MonitoredCall"]["VehicleAtStop"]),
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
    if len(directions) == 2:
        stmt = siri_db.update(Line).where(Line.operator_id == operator_id, Line.line_id == line_id).values(
            {
                "direction_0_id": directions[0]["DirectionId"],
                "direction_0_name": directions[0]["Name"],
                "direction_1_id": directions[1]["DirectionId"],
                "direction_1_name": directions[1]["Name"]
            })
    elif len(directions) == 1:
        stmt = siri_db.update(Line).where(Line.operator_id == operator_id, Line.line_id == line_id).values(
            {
                "direction_0_id": directions[0]["DirectionId"],
                "direction_0_name": directions[0]["Name"],
                "direction_1_id": None,
                "direction_1_name": None
            })
    else:
        raise Exception("Only 1 or 2 directions are supported")
    siri_db.session.execute(stmt)
    siri_db.session.commit()

    patterns_to_add = []
    for pattern in pattern_dict['journeyPatterns']:
        patterns_to_add.append(Pattern(operator_id=operator_id,
                                       line_id=pattern['LineRef'],
                                       pattern_id=pattern['serviceJourneyPatternRef'],
                                       pattern_name=pattern['Name'],
                                       pattern_direction=pattern['DirectionRef'],
                                       pattern_trip_count=pattern['TripCount']))
        save_stop_pattern(siri_db, operator_id, pattern['serviceJourneyPatternRef'], pattern['PointsInSequence'])

    patterns_to_delete = siri_db.delete(Pattern).where(Pattern.operator_id == operator_id,
                                                       Pattern.line_id == line_id)
    siri_db.session.execute(patterns_to_delete)
    siri_db.session.commit()

    siri_db.session.add_all(patterns_to_add)
    siri_db.session.commit()
    return None


def save_stop_pattern(siri_db: flask_sqlalchemy.SQLAlchemy,
                      operator_id: str,
                      pattern_id: str,
                      stop_pattern_dict: dict) -> None:
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

    untimed_stops = [StopPattern(operator_id=operator_id,
                                 pattern_id=pattern_id,
                                 stop_order=stop_pattern["Order"],
                                 stop_id=stop_pattern["ScheduledStopPointRef"],
                                 timing_point=False)
                     for stop_pattern in stop_pattern_dict['StopPointInJourneyPattern']]
    timed_stops = [StopPattern(operator_id=operator_id,
                               pattern_id=pattern_id,
                               stop_order=stop_pattern["Order"],
                               stop_id=stop_pattern["ScheduledStopPointRef"],
                               timing_point=True)
                   for stop_pattern in stop_pattern_dict['TimingPointInJourneyPattern']]

    stop_patterns_to_delete = siri_db.delete(StopPattern).where(StopPattern.operator_id == operator_id,
                                                                StopPattern.pattern_id == pattern_id)
    siri_db.session.execute(stop_patterns_to_delete)
    siri_db.session.commit()

    siri_db.session.add_all(untimed_stops + timed_stops)
    siri_db.session.commit()
    return None


def get_stop_monitoring_dict(transit_api_key, siri_base_url, operator_id):
    """
    Get stop monitoring from SIRI using api key and url

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
    return siri_client.stop_monitoring(agency=operator_id)


def parse_stop_monitoring_dict(operator_id: str, stop_monitoring_dict: dict) -> (Vehicle, OnwardCall):
    """
    Parses the stop monitoring dictionary and returns a dictionary of selected items

    :param operator_id: operator id
    :type operator_id: str

    :param stop_monitoring_dict: dictionary for a vehicle to be parsed
    :type stop_monitoring_dict: dict

    :return: Vehicle object and onward call object
    :rtype: Vehicle, OnwardCall
    """

    dataframe_ref = stop_monitoring_dict["MonitoredVehicleJourney"]["FramedVehicleJourneyRef"]["DataFrameRef"]
    vehicle = Vehicle(
        operator_id=operator_id,
        vehicle_journey_ref=stop_monitoring_dict["MonitoredVehicleJourney"]["FramedVehicleJourneyRef"][
            "DatedVehicleJourneyRef"],
        dataframe_ref_date=parse_time_str(dataframe_ref).date(),
        line_id=stop_monitoring_dict["MonitoredVehicleJourney"]["LineRef"],
        vehicle_direction=stop_monitoring_dict["MonitoredVehicleJourney"]["DirectionRef"],
        vehicle_longitude=parse_optional_floats(stop_monitoring_dict["MonitoredVehicleJourney"]["VehicleLocation"][
                                                    "Longitude"]),
        vehicle_latitude=parse_optional_floats(stop_monitoring_dict["MonitoredVehicleJourney"]["VehicleLocation"][
                                                   "Latitude"]),
        vehicle_bearing=parse_optional_floats(stop_monitoring_dict["MonitoredVehicleJourney"]["Bearing"])
    )
    onward_call = OnwardCall(
        operator_id=operator_id,
        vehicle_journey_ref=stop_monitoring_dict["MonitoredVehicleJourney"]["FramedVehicleJourneyRef"][
            "DatedVehicleJourneyRef"],
        dataframe_ref_date=parse_time_str(dataframe_ref).date(),
        stop_id=stop_monitoring_dict["MonitoredVehicleJourney"]["MonitoredCall"]["StopPointRef"],
        vehicle_at_stop=parse_bools(stop_monitoring_dict["MonitoredVehicleJourney"]["MonitoredCall"]["VehicleAtStop"]),
        aimed_arrival_time_utc=parse_time_str(stop_monitoring_dict["MonitoredVehicleJourney"]["MonitoredCall"][
                                                      "AimedArrivalTime"]),
        expected_arrival_time_utc=parse_time_str(stop_monitoring_dict["MonitoredVehicleJourney"]["MonitoredCall"][
                                                    "ExpectedArrivalTime"]),
        aimed_departure_time_utc=parse_time_str(stop_monitoring_dict["MonitoredVehicleJourney"]["MonitoredCall"][
                                                   "AimedDepartureTime"]),
        expected_departure_time_utc=parse_time_str(stop_monitoring_dict["MonitoredVehicleJourney"]["MonitoredCall"][
                                                      "ExpectedDepartureTime"])
    )

    return vehicle, onward_call


def save_stop_monitoring(siri_db,
                         operator_id: str,
                         stop_monitoring: dict,
                         current_time: dt.datetime) -> None:
    """
    Stores the vehicles and stop monitoring into the database.

    :param siri_db: database
    :type siri_db: flask_sqlalchemy.SQLAlchemy

    :param operator_id: operator id
    :type operator_id: str

    :param stop_monitoring: dictionary that contains the stops
    :type stop_monitoring: dict

    :param current_time: current utc time
    :type current_time: dt.datetime

    :return: None
    :rtype: None
    """

    monitored_stop_visits = stop_monitoring["ServiceDelivery"]["StopMonitoringDelivery"]["MonitoredStopVisit"]
    vehicles_to_add = []
    vehicle_tracker = set()
    onward_calls_to_add = []
    for monitored_stop_visit in monitored_stop_visits:
        vehicle, onward_call = parse_stop_monitoring_dict(operator_id,  monitored_stop_visit)
        vehicle_tuple = (vehicle.vehicle_journey_ref, vehicle.dataframe_ref_date)
        if not vehicle.contains_none() and vehicle_tuple not in vehicle_tracker:
            vehicles_to_add.append(vehicle)
            vehicle_tracker.add(vehicle_tuple)
        if onward_call:
            onward_calls_to_add.append(onward_call)

    vehicles_to_delete = siri_db.delete(Vehicle).where(Vehicle.operator_id == operator_id)
    siri_db.session.execute(vehicles_to_delete)
    siri_db.session.commit()
    siri_db.session.add_all(list(vehicles_to_add))
    siri_db.session.commit()

    onward_calls_to_delete = siri_db.delete(OnwardCall).where(OnwardCall.operator_id == operator_id)
    siri_db.session.execute(onward_calls_to_delete)
    siri_db.session.commit()
    siri_db.session.add_all(onward_calls_to_add)
    siri_db.session.commit()

    stmt = siri_db.update(Operator).where(Operator.operator_id == operator_id).values(
        stop_monitoring_updated=current_time)
    siri_db.session.execute(stmt)
    siri_db.session.commit()

    return None


def get_shapes_dict(transit_api_key: str,
                    siri_base_url: str,
                    operator_id: str,
                    trip_id: str) -> dict:
    """
    Get shape from SIRI using api key and url

    :param transit_api_key: api key
    :type transit_api_key: api key

    :param siri_base_url: url for the transit api
    :type siri_base_url: url for the transit api

    :param operator_id: operator id
    :type operator_id: str

    :param trip_id: trip id
    :type trip_id: str

    :return: dictionary containing the shape
    :rtype: dict
    """

    siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
    return siri_client.shapes(operator_id, trip_id)


def save_shapes(siri_db: flask_sqlalchemy.SQLAlchemy,
                operator_id: str,
                line_id: str,
                shape_dict: dict,
                current_time: dt.datetime) -> None:
    """
    Parses the stop monitoring dictionary and returns a dictionary of selected items

    :param siri_db: database
    :type siri_db: flask_sqlalchemy.SQLAlchemy

    :param operator_id: operator id
    :type operator_id: str

    :param line_id: line id
    :type line_id: str

    :param shape_dict: dictionary for a vehicle to be parsed
    :type shape_dict: dict

    :param current_time: current utc time
    :type current_time: dt.datetime

    :return: None
    :rtype: None
    """

    shape_coordinates_list = \
    shape_dict['Content']['TimetableFrame']['vehicleJourneys']['ServiceJourney']['LinkSequenceProjection'][
        'LineString']['pos']
    shape_coordinates_list = [x.split() for x in shape_coordinates_list]
    shape_coordinates_df = pd.DataFrame(shape_coordinates_list, columns=['latitude', 'longitude']).astype(float)
    shape_coordinates = [Shape(operator_id=operator_id,
                               line_id=line_id,
                               shape_order=ind,
                               shape_latitude=row['latitude'],
                               shape_longitude=row['longitude'])
                         for ind, row in shape_coordinates_df.iterrows()]

    shapes_to_delete = siri_db.delete(Shape)
    siri_db.session.execute(shapes_to_delete)
    siri_db.session.commit()
    siri_db.session.add_all(shape_coordinates)
    siri_db.session.commit()

    stmt = siri_db.update(Line).where(siri_db.and_(Line.operator_id == operator_id,
                                                   Line.line_id == line_id)).values(
        shape_updated=current_time)
    siri_db.session.execute(stmt)
    siri_db.session.commit()



def upcoming_vehicles(siri_db: flask_sqlalchemy.SQLAlchemy,
                      operator_id: str,
                      stop_id: str,
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

    stmt = siri_db.select(Vehicle, OnwardCall).join(OnwardCall).filter(siri_db.and_(
        OnwardCall.stop_id == stop_id, OnwardCall.operator_id == operator_id))
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
            response_dict[vehicle.line_id].append(eta_time)
    for key in response_dict.keys():
        response_dict[key] = [format_eta_time(eta_time) for eta_time in sorted(response_dict[key])]
    return response_dict


def get_stop_timetable_dict(transit_api_key: str,
                            siri_base_url: str,
                            operator_id: str,
                            stop_code: str
                            ) -> dict:
    """
    Get shape from SIRI using api key and url

    :param transit_api_key: api key
    :type transit_api_key: api key

    :param siri_base_url: url for the transit api
    :type siri_base_url: url for the transit api

    :param operator_id: operator id
    :type operator_id: str

    :param stop_code: stop id
    :type stop_code: str

    :return: dictionary containing the shape
    :rtype: dict
    """

    siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
    return siri_client.stop_timetable(operator_id, stop_code)



def save_stop_timetable(siri_db: flask_sqlalchemy.SQLAlchemy,
                        operator_id: str,
                        stop_id: str,
                        timetable_dict: dict) -> None:
    """
   Store stop timetable for a given stop in the database.

   :param siri_db: database
   :type siri_db: flask_sqlalchemy.SQLAlchemy

   :param operator_id: operator id
   :type operator_id: str

   :param stop_id: stop id
   :type stop_id: str

   :param timetable_dict: dictionary containing timetable for a given stop
   :type timetable_dict: dict

   :return: None
   :rtype: None
   """
    timetable_list = timetable_dict["Siri"]["ServiceDelivery"]["StopTimetableDelivery"]["TimetabledStopVisit"]
    stop_timetable_list = [StopTimetable(operator_id=operator_id,
                                         vehicle_journey_ref=timetable["TargetedVehicleJourney"][
                                             "DatedVehicleJourneyRef"],
                                         stop_id=timetable["MonitoringRef"],
                                         aimed_arrival_time_utc=parse_time_str(timetable["TargetedVehicleJourney"][
                                                                                   "TargetedCall"]["AimedArrivalTime"]),
                                         aimed_departure_time_utc=parse_time_str(
                                             timetable["TargetedVehicleJourney"]["TargetedCall"]["AimedDepartureTime"])
                                         )
                           for timetable in timetable_list]

    stop_timetable_to_delete = siri_db.delete(StopTimetable).where(StopTimetable.operator_id == operator_id,
                                                                   StopTimetable.stop_id == stop_id)
    siri_db.session.execute(stop_timetable_to_delete)
    siri_db.session.commit()

    siri_db.session.add_all(stop_timetable_list)
    siri_db.session.commit()

    return None


def determine_vehicle_ref_full_journey(siri_db: flask_sqlalchemy.SQLAlchemy,
                                       operator_id: str,
                                       beg_stop_code: str,
                                       end_stop_code: str,
                                       ) -> str:
    """
    Determine a vehicle that travels the full length of the route

   :param siri_db: database
   :type siri_db: flask_sqlalchemy.SQLAlchemy

   :param operator_id: operator id
   :type operator_id: str

   :param beg_stop_code: stop id for first stop
   :type beg_stop_code: str

   :param end_stop_code: stop id for last stop
   :type end_stop_code: str

   :return: vehicle_journey_ref
   :rtype: str
    """
    query = siri_db.session.query(StopTimetable.vehicle_journey_ref,
                                  func.count(StopTimetable.vehicle_journey_ref)
                                  ).group_by(StopTimetable.vehicle_journey_ref).having(func.count(StopTimetable.vehicle_journey_ref) > 1)

    result = siri_db.session.execute(query).all()
    return result[0][0]




def read_key_api_file() -> (str, str):
    """
    Reads the key and url form the environmental variables

    :return: tuple containing key and url
    :rtype: tuple(str, str)
    """
    return os.environ.get("API_KEY"), os.environ.get("BASE_URL")


def refresh_needed(siri_db: flask_sqlalchemy.SQLAlchemy,
                   operator_id: str,
                   table_name: str,
                   refresh_limit: float,
                   current_time: dt.datetime) -> bool:
    """
    Determines if refresh of a given table is needed.

    :param siri_db: database
   :type siri_db: flask_sqlalchemy.SQLAlchemy

    :param operator_id: ID for the operator
    :type operator_id: str

    :param table_name: name of the table to be checked
    :type table_name: str

    :param refresh_limit: minimum time to elapse before refreshing table
    :type refresh_limit: float

    :param current_time: current time in utc
    :type refresh_limit: dt.datetime

    :return: boolean for if the table should be refreshed
    :rtype: bool
    """
    operator = siri_db.session.execute(siri_db.select(Operator).filter_by(operator_id=operator_id)).scalar_one()
    last_update_time = operator.__dict__[table_name]
    if last_update_time is None:
        return True
    delta_time = current_time.replace(tzinfo=None) - last_update_time
    return delta_time >= dt.timedelta(minutes=refresh_limit)


def operator_refresh_needed(siri_db: flask_sqlalchemy.SQLAlchemy,
                            refresh_limit: float,
                            current_time: dt.datetime) -> bool:
    """
    Determines if refresh of a given table is needed.

    :param siri_db: database
    :type siri_db: flask_sqlalchemy.SQLAlchemy

    :param refresh_limit: minimum time to elapse before refreshing table
    :type refresh_limit: float

    :param current_time: current time in utc
    :type refresh_limit: dt.datetime

    :return: boolean for if the table should be refreshed
    :rtype: bool
    """

    operator_refresh_time = siri_db.session.execute(siri_db.select(Parameter).filter_by(
        name="operator_refresh_time")).scalar_one_or_none()
    if operator_refresh_time is None:
        return True
    last_update_time = dateutil.parser.isoparse(operator_refresh_time.value).replace(tzinfo=None)
    delta_time = current_time.replace(tzinfo=None) - last_update_time
    return delta_time >= dt.timedelta(minutes=refresh_limit)


def save_operator_refresh_time(siri_db: flask_sqlalchemy.SQLAlchemy,
                               current_time: dt.datetime) -> None:
    """
    Determines if refresh of a given table is needed.

    :param siri_db: database
    :type siri_db: flask_sqlalchemy.SQLAlchemy

    :param current_time: current time in utc
    :type current_time: dt.datetime

    :return: boolean for if the table should be refreshed
    :rtype: bool
    """
    operator_refresh = Parameter("operator_refresh_time", current_time.isoformat())
    siri_db.session.add(operator_refresh)
    siri_db.session.commit()


def parse_time_str(time_str: typing.Optional[str] = None) -> typing.Union[dt.datetime, None]:
    """
    Parses the time string and returns datetime object if time string is not none. If none, returns none.

    :param time_str: string that would be converted to datetime object
    :type time_str: str

    :return: datetime object
    :rtype: dt.datetime
    """
    if time_str is None:
        return None
    else:
        dt_obj = dateutil.parser.isoparse(time_str)
        if dt_is_timezone_aware(dt_obj):
            return dt_obj.astimezone(dateutil.tz.UTC).replace(tzinfo=None)
        else:
            return dt_obj


def dt_is_timezone_aware(dt_obj: dt.datetime) -> bool:
    """
    Checks if a given datetime object is timezone aware.

    :param dt_obj: minimum time to elapse before refreshing table
    :type dt_obj: dt.datetime

    :return: Returns True if the datetime object is timezone aware, False otherwise.
    :rtype: bool
    """
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


def parse_optional_floats(value: str) -> typing.Union[float, None]:
    """
    Parses the optional number string.

    :param value: string that contains a number or is empty
    :type value: str

    :return: float if string contains a number or None if string is empty
    :rtype: float or None
    """
    if value:
        return float(value)
    else:
        return None


def parse_bools(value: str) -> bool:
    """
    Convert a string that has a bool value to boolean.

    :param value: string that contains a boolean or is empty
    :type value: str

    :return: boolean value
    :rtype: bool
    """
    if value is True or value == 'true':
        return True
    elif value is False or value == 'false':
        return False
    elif value == '':
        return False
    else:
        raise ValueError(f"parse_bools expected true or false, got {value}")


def sort_response_dict(input_dict) -> OrderedDict:
    """
    Returns an ordered dict for the arrival times.

    :param input_dict: dictionary that contains expected arrival times
    :type input_dict: dict

    :return: sorted dictionary of the arrival times
    :rtype: bool
    """
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
