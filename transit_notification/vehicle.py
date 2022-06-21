import pandas as pd
import dateutil.parser as dp
import numpy as np

STOP_DF_TIME_COLS = ["AimedArrivalTime", "ExpectedArrivalTime", "AimedDepartureTime", "ExpectedDepartureTime"]


class Vehicle:
    def __init__(self, input_dict: dict):
        """
        Create vehicle using data quiered  from 511.org

        :param input_dict: dictionary containing information on a vehicle
        :type input_dict: dict
        """

        self.recorded_at_time = dp.parse(input_dict["RecordedAtTime"])
        monitored_vehicle_journey = input_dict["MonitoredVehicleJourney"]
        self.line_ref = monitored_vehicle_journey["LineRef"]
        self.line_name = monitored_vehicle_journey["PublishedLineName"]
        self.direction = monitored_vehicle_journey["DirectionRef"]
        self.vehicle_journey_ref = monitored_vehicle_journey["FramedVehicleJourneyRef"]["DatedVehicleJourneyRef"]
        self.longitude = float(monitored_vehicle_journey["VehicleLocation"]["Longitude"])
        self.latitude = float(monitored_vehicle_journey["VehicleLocation"]["Latitude"])
        monitored_call = monitored_vehicle_journey["MonitoredCall"]
        next_stop = {
            "StopPointRef": monitored_call["StopPointRef"],
            "StopPointName": monitored_call["StopPointName"],
            "AimedArrivalTime": monitored_call["AimedArrivalTime"],
            "ExpectedArrivalTime": monitored_call["ExpectedArrivalTime"],
            "AimedDepartureTime": monitored_call["AimedDepartureTime"],
            "ExpectedDepartureTime": monitored_call["ExpectedDepartureTime"]
        }
        if "OnwardCalls" in monitored_vehicle_journey:
            future_stops = monitored_vehicle_journey["OnwardCalls"]["OnwardCall"]
            future_stops.insert(0, next_stop)
        else:
            future_stops = [next_stop]
        self.stops = self.parse_stops(pd.DataFrame(future_stops))

    @staticmethod
    def parse_stops(df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert stop time information from string to DateTime. Add departure and arrival delay columns.

        :param df: string that contains the api key for 511.org
        :type df: Pandas DataFrame

        :return: parsed DataFrame
        :rtype: Pandas DataFrame
        """

        for col in STOP_DF_TIME_COLS:
            df[col] = pd.to_datetime(df[col], format="%Y-%m-%dT%H:%M:%SZ", utc=True)
        df["DepartureDelay"] = df["ExpectedDepartureTime"] - df["AimedDepartureTime"]
        df["ArrivalDelay"] = df["ExpectedArrivalTime"] - df["AimedArrivalTime"]
        return df

    def is_vehicle_delayed(self, delay_amount) -> bool:
        """
        Determine if the vehicle delayed more than amount specified.

        :param delay_amount: Allowed delay in minutes before flagging vehicle as delayed
        :type delay_amount: float

        :return: Returns true if train delayed
        :rtype: bool
        """
        delay_criteria = np.timedelta64(delay_amount, 'm')
        delayed_deperature = (self.stops["DepartureDelay"] > delay_criteria).any()
        delayed_arrival = (self.stops["ArrivalDelay"] > delay_criteria).any()
        return delayed_deperature or delayed_arrival



    """
    For caltrain, delay messages should contain vehicle_journey_ref
    for sfmta, delay message should contain line_ref

    vehicle monitoring is good for simple systems - caltrain
    stop monitoring would be good for complex - sfmta

    data is stored in slightly different formats for vehicle and stop monitoring
    """
