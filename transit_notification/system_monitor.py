import pandas as pd
from geopy import distance
from zoneinfo import ZoneInfo
import numpy as np
import matplotlib.pyplot as plt

import siri_transit_api_client
import configparser
import vehicle as vh


# import the configuration file which has the api keys
config = configparser.ConfigParser()
config.read("../config.ini")
transit_api_key = config["keys"]["Transit511Key"]
operator_name="SF"

siri_client = siri_transit_api_client.SiriClient(api_key=transit_api_key)

vehicle_monitoring = siri_client.vehicle_monitoring(agency=operator_name)

vehicle_dict_list = vehicle_monitoring['Siri']["ServiceDelivery"]["VehicleMonitoringDelivery"]['VehicleActivity']
stop_list =[]
vehicle_list = []
for vehicle_dict in vehicle_dict_list:
    vehicle = vh.Vehicle(vehicle_dict)
    stop_list.append(vehicle.output_stops_df())
    vehicle_list.append(vehicle.output_vehicle_ser())

vehicle_df = pd.DataFrame(vehicle_list)
stop_df = pd.concat(stop_list, ignore_index=True)

stop_id = "15557"
route_name = "14R"
selected_stop = stop_df[stop_df['StopPointRef'] == stop_id]
selected_stop = pd.merge(selected_stop, vehicle_df, on=['DatedVehicleJourneyRef', 'DataFrameRef'])
stop_name = selected_stop.StopPointName.values[0]
selected_buses = selected_stop[selected_stop["LineRef"] == route_name]
expected_times = sorted(selected_buses["ArrivalDeltaMin"].values)

message_body = f"Route: {route_name}\nStop: {stop_name}\nStop ID: {stop_id}\nNext arrivals: "
for ind in range(len(expected_times)):
    message_body = message_body + f"{expected_times[ind]} min"
    if ind < len(expected_times) - 1:
        message_body = message_body + ", "

print(message_body)

# routes experiencing delays
delay_amount = 5
delay_criteria = np.timedelta64(delay_amount, 'm')
delayed_buses = pd.merge(stop_df[stop_df["ArrivalDelta"] > delay_criteria],
                         vehicle_df,
                         on=['DatedVehicleJourneyRef', 'DataFrameRef'])
delayed_bus_lines = sorted(delayed_buses["LineRef"].unique())

# create a histograms of delays
buses = pd.merge(stop_df, vehicle_df, on=['DatedVehicleJourneyRef', 'DataFrameRef'])
buses["ArrivalDelta"].dt.total_seconds().plot.hist()
plt.show()
