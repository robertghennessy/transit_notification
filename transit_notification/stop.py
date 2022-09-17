import pandas as pd
import dateutil.parser as dp
import numpy as np
import datetime as dt
from zoneinfo import ZoneInfo


class Stop:
    def __init__(self, input_dict: dict):
        """
        Create stop by parsing data queried from 511.org

        :param input_dict: dictionary containing information on a vehicle
        :type input_dict: dict
        """

        self.id = input_dict["id"]
        self.name = input_dict["Name"]
        self.longitude = input_dict["Location"]["Longitude"]
        self.latitude = input_dict["Location"]["Latitude"]

    def output_series(self) -> pd.Series:
        """
        Output the stops dataframe for potential storage.

        :return: parsed Series
        :rtype: Pandas Series
        """
        return pd.Series(self.__dict__)
