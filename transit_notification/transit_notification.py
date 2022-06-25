"""Main module."""
import os
import dateutil.parser as dp
import datetime as dt
import json
import pandas as pd
from geopy import distance
from zoneinfo import ZoneInfo
import numpy as np

import vehicle as vh

"""
Steps
1. Query operators and confirm that operator has vehicles monitoring
2. Parse the data into vehicles
3. construct information to send to push notification

"""
# Configuration file
operator_name = "SF"
route_name = "14"
direction_id = "IB"
# can get the following from google maps
stop_coordinates = {"lat": 37.759565551910285, "long": -122.41900156132917} # nearest stop = 15557
local_tz = ZoneInfo('America/Los_Angeles')
utc = ZoneInfo('UTC')

# Check if operator is valid
with open("/Users/roberthennessy/Documents/python_project/json/sfmta/operators.json", "r") as file:
    operators_dict = json.load(file)

operators_df = pd.DataFrame(operators_dict)
if operator_name not in operators_df["Id"].values:
    raise ValueError("Invalid operator short name.")
if not operators_df.loc[operators_df["Id"] == operator_name, "Monitored"].all():
    raise ValueError("Vehicles not monitored")

# check if valid route id
with open("/Users/roberthennessy/Documents/python_project/json/sfmta/lines.json", "r") as file:
    lines_dict = json.load(file)

routes_df = pd.DataFrame(lines_dict)
if route_name not in routes_df["Id"].values:
    raise ValueError("Invalid route id.")
if not routes_df.loc[routes_df["Id"] == route_name, "Monitored"].all():
    raise ValueError("Vehicles not monitored for specified route. ")

with open("/Users/roberthennessy/Documents/python_project/json/sfmta/patterns_route_14.json", "r") as file:
    patterns_dict = json.load(file)

direction_df = pd.DataFrame(patterns_dict['directions'])
if direction_df not in direction_df["DirectionId"].values:
    raise ValueError("Invalid route id.")

with open("/Users/roberthennessy/Documents/python_project/json/sfmta/stops_route_14_IB.json", "r") as file:
    stops_dict = json.load(file)

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

with open("/Users/roberthennessy/Documents/python_project/json/sfmta/stop_monitoring_15557.json", "r") as file:
    stop_monitoring = json.load(file)

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
    expected_time.append(veh["ArrivalDelta"].dt.total_seconds().values[0])

expected_time = np.floor(np.array(expected_time) / 60)
expected_time = expected_time.astype(int)

message_body = f"Route: {route_name}\nStop: {nearest_stop_name}\nStop ID: {nearest_stop_id}\nNext arriavals: "
message_body = message_body + f"{expected_time[0]} min, {expected_time[1]} min, {expected_time[2]} min"

print(message_body)
print(len(message_body))
