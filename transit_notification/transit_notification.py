"""Main module."""
import os
import dateutil.parser as dp
import datetime as dt
import json
import pandas as pd

import vehicle as vh

"""
Steps
1. Query operators and confirm that operator has vehicles monitoring
2. Parse the data into vehicles
3. construct information to send to push notification

"""

with open("/Users/roberthennessy/Documents/python_project/json/sfmta/operators.json", "r") as file:
    operators_dict = json.load(file)

operators_df = pd.DataFrame(operators_dict)

operator_name = "CT"

# slices dataframe to allow printing of Id and short names
#print(operators_df[["Id", "ShortName"]])

if operator_name not in operators_df["Id"].values:
    print("Invalid operator short name")
if not operators_df[operators_df["Id"] == operator_name]["Monitored"].all():
    print("Vehicles not monitored")

with open("/Users/roberthennessy/Documents/python_project/json/caltrain/vehicle_monitoring.json", "r") as file:
    vehicle_monitoring_dict = json.load(file)
# check the time of the response
response_timestamp = dp.parse(vehicle_monitoring_dict["Siri"]["ServiceDelivery"]["VehicleMonitoringDelivery"]
                              ["ResponseTimestamp"])
utc_now = dt.datetime.utcnow()
# TODO - add code to check that the response time is within 2 minutes of current time
vehicles = []
vehicle_list = vehicle_monitoring_dict["Siri"]["ServiceDelivery"]["VehicleMonitoringDelivery"]["VehicleActivity"]
print(vehicle_list)
for vehicle in vehicle_list:
    vehicles.append(vh.Vehicle(vehicle))

#delayed_trains_message = [vehicle.delay_message for vehicle in vehicles if vehicle.delay_message is not None]

tst_vehicle = vehicles[0]
print(type(tst_vehicle))
print(tst_vehicle.__dict__)

with open("/Users/roberthennessy/Documents/python_project/json/caltrain/stop_monitoring.json", "r") as file:
    stop_monitoring_dict = json.load(file)

tst_stop = stop_monitoring_dict["ServiceDelivery"]["StopMonitoringDelivery"]["MonitoredStopVisit"]
print(vh.Vehicle(tst_stop[0]).__dict__)
