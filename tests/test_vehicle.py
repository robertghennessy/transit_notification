import pytest
import json
import os
from transit_notification import vehicle
import datetime as dt

#TODO - need import tzutc()

class TestVehicles:

    def test_file_read(self):
        with open("../test_jsons/vehicle_monitoring.json", "r") as file:
            test_vehicle = json.load(file)
        print(test_vehicle)
        assert type(test_vehicle) is dict

    def test_vehicle_init(self):
        with open("../test_jsons/vehicle_monitoring.json", "r") as file:
            vehicle_monitoring_response = json.load(file)
        test_vehicles = vehicle_monitoring_response["Siri"]["ServiceDelivery"]["VehicleMonitoringDelivery"][
            "VehicleActivity"]
        test_vehicle = vehicle.Vehicle(test_vehicles[0])
        #assert test_vehicle.recorded_at_time == dt.datetime(2022, 6, 8, 22, 45, 15, tzinfo=tzutc())
        assert test_vehicle.line_ref == "L1"
        assert test_vehicle.line_name == "Local"
        assert test_vehicle.direction == "S"
        assert test_vehicle.vehicle_journey_ref == "122"
        assert test_vehicle.longitude == -122.193558
        assert test_vehicle.latitude == 37.4618797
        assert test_vehicle.stops.StopPointRef[0] == "70162"

        #assert test_vehicle.stops.AimedArrivalTime[0] == dt.datetime(2022, 6, 8, 22, 38, 0, tzinfo=tzutc())
        #assert test_vehicle.stops.ExpectedArrivalTime[0] == dt.datetime(2022, 6, 8, 22, 44, 29, tzinfo=tzutc())
        #assert test_vehicle.stops.AimedDepartureTime[0] == dt.datetime(2022, 6, 8, 22, 38, 0, tzinfo=tzutc())
        #assert test_vehicle.stops.ExpectedDepartureTime[0] == dt.datetime(2022, 6, 8, 22, 45, 29, tzinfo=tzutc())

        assert test_vehicle.stops.ArrivalDelay[0] == dt.timedelta(minutes=6, seconds=29)
        assert test_vehicle.stops.DepartureDelay[0] == dt.timedelta(minutes=7, seconds=29)

    def test_vehicle_delayed(self):
        with open("../test_jsons/vehicle_monitoring.json", "r") as file:
            vehicle_monitoring_response = json.load(file)
        test_vehicles = vehicle_monitoring_response["Siri"]["ServiceDelivery"]["VehicleMonitoringDelivery"][
            "VehicleActivity"]
        test_vehicle = vehicle.Vehicle(test_vehicles[0])
        assert test_vehicle.is_vehicle_delayed(5) == True
        assert test_vehicle.is_vehicle_delayed(10) == False

