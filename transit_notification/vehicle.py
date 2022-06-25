import pandas as pd
import dateutil.parser as dp
import numpy as np
import datetime as dt
from zoneinfo import ZoneInfo


STOP_DF_TIME_COLS = ["AimedArrivalTime", "ExpectedArrivalTime", "AimedDepartureTime", "ExpectedDepartureTime"]
utc = ZoneInfo('UTC')

class Vehicle:
    def __init__(self, input_dict: dict):
        """
        Create vehicle by parsing data queried from 511.org

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
        if "MonitoredCall" in monitored_vehicle_journey:
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
        utc_now = dt.datetime.utcnow().replace(tzinfo=utc)
        for col in STOP_DF_TIME_COLS:
            df[col] = pd.to_datetime(df[col], format="%Y-%m-%dT%H:%M:%SZ", utc=True)
        df["DepartureDelay"] = df["ExpectedDepartureTime"] - df["AimedDepartureTime"]
        df["ArrivalDelay"] = df["ExpectedArrivalTime"] - df["AimedArrivalTime"]
        df["DepartureDelta"] = df["ExpectedDepartureTime"] - utc_now
        df["ArrivalDelta"] = df["ExpectedArrivalTime"] - utc_now
        return df

    def output_series(self) -> pd.Series:
        """
        Convert the object to a Pandas Series.

        :return: Pandas Series
        :rtype: Pandas Series
        """
        return pd.Series(self.__dict__)

    def is_vehicle_delayed(self, delay_amount) -> bool:
        """
        Determine if the vehicle delayed more than a given number of minutes.

        :param delay_amount: Allowed delay in minutes before flagging vehicle as delayed
        :type delay_amount: float

        :return: Returns true if train delayed
        :rtype: bool
        """
        delay_criteria = np.timedelta64(delay_amount, 'm')
        delayed_deperature = (self.stops["DepartureDelay"] > delay_criteria).any()
        delayed_arrival = (self.stops["ArrivalDelay"] > delay_criteria).any()
        return delayed_deperature or delayed_arrival

    def delay_message(self, journey_name_switch: int = 1, monitor_arrival: bool = True,  stop_id: str = None) -> str:
        """
        Create the delay message for a vehicle.

        :param journey_name_switch: Selects the
        :type journey_name_switch: int

        :param monitor_arrival: If true, return arrival delays. If false, return departure delays
        :type monitor_arrival: bool

        :param stop_id: Allowed delay in minutes before flagging vehicle as delayed
        :type stop_id: str, optional

        :return: Returns true if train delayed
        :rtype: bool
        """
        statement_dict = {}
        if journey_name_switch == 1:
            statement_dict["journey_name"] = self.vehicle_journey_ref
        elif journey_name_switch == 2:
            statement_dict["journey_name"] = journey_name = self.line_ref
        else:
            raise ValueError("journey_name_switch can only have a value of 1 or 2")

        if stop_id:
            ser = self.stops[self.stops == stop_id]  # TODO - need to convert to series
        else:
            ser = self.stops.iloc[0]  # this is already a series









    def print_time_delta(self, time_delta) -> str:
        """

        """
        components = time_delta.components
        return f"{components.hours:02}:{components.minutes:02}:{components.seconds:02}"



    """
    For caltrain, delay messages should contain vehicle_journey_ref -
    for sfmta, delay message should contain line_ref

    vehicle monitoring is good for simple systems - caltrain
    stop monitoring would be good for complex - sfmta

    vehicle monitoring provides more information than stop monitoring.
    data is stored in slightly different formats for vehicle and stop monitoring
    """
    # want to print something for a given vehicle
    # with delay, 201 San Mateo 06:30 -> 06:45
    # no delay, 201 San Mateo 06:30
