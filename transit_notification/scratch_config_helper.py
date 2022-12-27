"""
Description: This file helps provides information helpful for configuration.

@author: Robert Hennessy (robertghennessy@gmail.com)
"""

import pandas as pd
import os
from geopy import distance

import siri_transit_api_client
import configparser


# import the configuration file which has the api keys
config = configparser.ConfigParser()
config.read("../key_api.ini")
transit_api_key = config["keys"]["Transit511Key"]

siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key)

directory = config["config_helper"]["directory_location"]
operator_name = "SF"
route_name = "14"
stops_coordinates = [
    {"lat": 37.759565551910285, "long": -122.41900156132917},
    {"lat": 37.78661636170893, "long": -122.40146090892988}
]

if operator_name is None:
    operators_dict = siri_client.operators()
    operators_df = pd.DataFrame(operators_dict)
    operators_df = operators_df[['Id', 'Name', 'Monitored']]
    operators_df.to_csv(os.path.join(directory, "operators.csv"))

if route_name is None:
    lines_dict = siri_client.lines(operator_name)
    routes_df = pd.DataFrame(lines_dict)
    routes_df = routes_df[['Id', 'Name', 'Monitored']]
    routes_df.to_csv(os.path.join(directory, "routes.csv"))

if stops_coordinates is None:
    stops_dict = siri_client.stops(operator_id=operator_name)
    stops_df = pd.json_normalize(stops_dict["Contents"]["dataObjects"]["ScheduledStopPoint"])
    stops_df['Location.Latitude'] = pd.to_numeric(stops_df['Location.Latitude'], errors='coerce')
    stops_df['Location.Longitude'] = pd.to_numeric(stops_df['Location.Longitude'], errors='coerce')
    stops_df = stops_df[['id', 'Name', 'Location.Latitude', 'Location.Longitude']]
    stops_df.to_csv(os.path.join(directory, "stops.csv"))

if stops_coordinates is not None:
    stops_dict = siri_client.stops(operator_id=operator_name)
    stops_df = pd.json_normalize(stops_dict["Contents"]["dataObjects"]["ScheduledStopPoint"])
    stops_df['Location.Latitude'] = pd.to_numeric(stops_df['Location.Latitude'], errors='coerce')
    stops_df['Location.Longitude'] = pd.to_numeric(stops_df['Location.Longitude'], errors='coerce')
    stop_results = []
    for ind, stop_coordinates in enumerate(stops_coordinates):
        stops_df['distance_km'] = stops_df.apply(lambda row: distance.distance(
            (row["Location.Latitude"], row["Location.Longitude"]), (stop_coordinates["lat"], stop_coordinates["long"])),
                                                 axis=1)
        stops_df = stops_df.sort_values(by='distance_km')
        nearest_stop = stops_df.iloc[0].copy()
        stop_results.append(nearest_stop)
    selected_stops_df = pd.DataFrame(stop_results)
    selected_stops_df.to_csv(os.path.join(directory, "selected_stops.csv"))
