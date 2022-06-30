"""Main module."""
import pandas as pd
from geopy import distance
from zoneinfo import ZoneInfo
import numpy as np

import siri_transit_api_client
import configparser
import vehicle as vh


# import the configuration file which has the api keys
config = configparser.ConfigParser()
config.read("../config.ini")
transit_api_key = config["keys"]["Transit511Key"]

siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key)


# Configuration
operator_name = "CT"
route_name = "14"
direction_id = "IB"
# can get the following from Google Maps
stop_coordinates = {"lat": 37.759565551910285, "long": -122.41900156132917}
local_tz = ZoneInfo('America/Los_Angeles')
utc = ZoneInfo('UTC')

# Check if operator is valid
operators_dict = siri_client.operators()

operators_df = pd.DataFrame(operators_dict)
if operator_name not in operators_df["Id"].values:
    raise ValueError("Invalid operator short name.")
if not operators_df.loc[operators_df["Id"] == operator_name, "Monitored"].all():
    raise ValueError("Vehicles not monitored")

# check if valid route id
lines_dict = siri_client.lines(operator_name)

routes_df = pd.DataFrame(lines_dict)
if route_name not in routes_df["Id"].values:
    raise ValueError("Invalid route id.")
if not routes_df.loc[routes_df["Id"] == route_name, "Monitored"].all():
    raise ValueError("Vehicles not monitored for specified route. ")

patterns_dict = siri_client.patterns(operator_name, route_name)
direction_df = pd.DataFrame(patterns_dict['directions'])
if direction_id not in direction_df["DirectionId"].values:
    raise ValueError("Invalid directions.")

stops_dict = siri_client.stops(operator_id=operator_name, line_id=route_name, direction_id=direction_id)

stops_df = pd.json_normalize(stops_dict["Contents"]["dataObjects"]["ScheduledStopPoint"])
stops_df['Location.Latitude'] = pd.to_numeric(stops_df['Location.Latitude'], errors='coerce')
stops_df['Location.Longitude'] = pd.to_numeric(stops_df['Location.Longitude'], errors='coerce')
stops_df['distance_km'] = stops_df.apply(lambda row: distance.distance(
    (row["Location.Latitude"], row["Location.Longitude"]), (stop_coordinates["lat"], stop_coordinates["long"])),
                                axis=1)
stops_df = stops_df.sort_values(by='distance_km')
nearest_stop = stops_df.iloc[0]
nearest_stop_id = nearest_stop["id"]
nearest_stop_name = nearest_stop["Name"]

stop_monitoring = siri_client.stop_monitoring(agency=operator_name, stop_code=nearest_stop_id)

vehicles = []
vehicle_list = stop_monitoring["ServiceDelivery"]["StopMonitoringDelivery"]["MonitoredStopVisit"]
for count, vehicle in enumerate(vehicle_list):
    vehicles.append(vh.Vehicle(vehicle).output_series())

stop_monitoring_df = pd.DataFrame(vehicles)
filter_line_ref = stop_monitoring_df["line_ref"] == route_name
filter_direction = stop_monitoring_df["direction"] == direction_id
stop_monitoring_df = stop_monitoring_df.loc[filter_line_ref & filter_direction]

upcoming_vehicles = stop_monitoring_df["stops"].values
expected_time = []
for veh in upcoming_vehicles:
    expected_time.append(veh["ArrivalDeltaMin"].values[0])

message_body = f"Route: {route_name}\nStop: {nearest_stop_name}\nStop ID: {nearest_stop_id}\nNext arrivals: "
for ind in range(len(expected_time)):
    message_body = message_body + f"{expected_time[ind]} min"
    if ind < len(expected_time) - 1:
        message_body = message_body + ", "

print(message_body)
print(len(message_body))
