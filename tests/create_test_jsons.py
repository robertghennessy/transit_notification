import configparser
import os
import datetime as dt
import json
import siri_transit_api_client
import dateutil.parser
import typing
import pandas as pd
import copy

json_folder = './test_input_jsons'

selected_operators = ['SF', 'CT', 'CE']
selected_operator = 'SF'
selected_line = '14'
selected_stops = ['15553', '15551']
selected_stop = '15553'
selected_lines = ['14', '49']
new_time = dt.datetime(2023, 9, 26, 15, 0, 0, 0, dt.timezone.utc)

vehicle_test_cases = [{'Name': 'Schedule_0-Est_0',
                       'ScheduledArrival': dt.timedelta(minutes=0),
                       'EstimatedArrival': dt.timedelta(minutes=0)},
                      {'Name': 'Schedule_10-Est_13',
                       'ScheduledArrival': dt.timedelta(minutes=10),
                       'EstimatedArrival': dt.timedelta(minutes=13)},
                      {'Name': 'Schedule_20-Est_16',
                       'ScheduledArrival': dt.timedelta(minutes=20),
                       'EstimatedArrival': dt.timedelta(minutes=16)},
                      {'Name': 'Schedule_40-Est_40',
                       'ScheduledArrival': dt.timedelta(minutes=40),
                       'EstimatedArrival': dt.timedelta(minutes=40)}]

stop_monitoring_test_cases = [{'Name': 'Schedule_0-Est_0_First_Stop',
                               'ScheduledArrival': dt.timedelta(minutes=0),
                               'EstimatedArrival': dt.timedelta(minutes=0)},
                              {'Name': 'Schedule_0-Est_0_Second_Stop',
                               'ScheduledArrival': dt.timedelta(minutes=2),
                               'EstimatedArrival': dt.timedelta(minutes=2)},
                              {'Name': 'Schedule_10-Est_13',
                               'ScheduledArrival': dt.timedelta(minutes=10),
                               'EstimatedArrival': dt.timedelta(minutes=13)},
                              {'Name': 'Schedule_20-Est_16',
                               'ScheduledArrival': dt.timedelta(minutes=20),
                               'EstimatedArrival': dt.timedelta(minutes=16)},
                              {'Name': 'Schedule_40-Est_40',
                               'ScheduledArrival': dt.timedelta(minutes=40),
                               'EstimatedArrival': dt.timedelta(minutes=40)}]


def create_operator_json(siri_client: siri_transit_api_client.siri_client.SiriClient,
                         operators: list,
                         folder: str) -> None:
    """
    Create a json of selected operators.
    """
    siri_operators = siri_client.operators()

    operator_list = []

    for operator in siri_operators:
        if operator['Id'] in operators:
            operator_list.append(operator)

    file_path = os.path.join(folder, 'operators.json')
    with open(file_path, 'w') as outfile:
        json.dump(operator_list, outfile, indent=4)


def create_lines_json(siri_client: siri_transit_api_client.siri_client.SiriClient,
                      operator: str,
                      lines: list,
                      folder: str) -> None:
    """
    Create a json of selected lines.
    """
    siri_lines = siri_client.lines(operator_id=operator)
    line_list = []
    for line in siri_lines:
        if line['Id'] in lines:
            line_list.append(line)

    file_path = os.path.join(folder, 'lines.json')
    with open(file_path, 'w') as outfile:
        json.dump(line_list, outfile, indent=4)


def create_stops_json(siri_client: siri_transit_api_client.siri_client.SiriClient,
                      operator: str,
                      stops: list,
                      new_time_dt: dt.datetime,
                      folder: str) -> None:
    """
    Create a json for selected stops.
    """

    stops_dict = siri_client.stops(operator_id=operator)
    stop_list = stops_dict['Contents']['dataObjects']['ScheduledStopPoint']
    new_stop_list = []
    for stop in stop_list:
        if stop['id'] in stops:
            new_stop_list.append(stop)

    stops_dict['Contents']['dataObjects']['ScheduledStopPoint'] = new_stop_list
    stops_dict['Contents']['ResponseTimestamp'] = new_time_dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    file_path = os.path.join(folder, 'stops.json')
    with open(file_path, 'w') as outfile:
        json.dump(stops_dict, outfile, indent=4)


def create_patterns_json(siri_client: siri_transit_api_client.siri_client.SiriClient,
                         operator: str,
                         line: str,
                         folder: str) -> None:
    """
    Create a json for the selected pattern. Selection based on operator and line.
    """
    patterns = siri_client.patterns(operator, line)
    file_path = os.path.join(folder, 'patterns.json')
    with open(file_path, 'w') as outfile:
        json.dump(patterns, outfile, indent=4)


def create_vehicle_monitoring_json(siri_client: siri_transit_api_client.siri_client.SiriClient,
                                   operator: str,
                                   folder: str) -> None:
    """
    Create a json for vehicle monitoring of the operator.
    """
    vehicle_monitoring = siri_client.vehicle_monitoring(operator)
    file_path = os.path.join(folder, 'vehicle_monitoring.json')
    with open(file_path, 'w') as outfile:
        json.dump(vehicle_monitoring, outfile, indent=4)


def create_stop_timetable_json(siri_client: siri_transit_api_client.siri_client.SiriClient,
                               operator: str,
                               stop_code: str,
                               folder: str) -> None:
    """
    Create a json for the stop timetable for a given operator and code.
    """
    stop_timetable = siri_client.stop_timetable(operator, stop_code)
    file_path = os.path.join(folder, 'stop_timetable.json')
    with open(file_path, 'w') as outfile:
        json.dump(stop_timetable, outfile, indent=4)


def create_holidays_json(siri_client: siri_transit_api_client.siri_client.SiriClient,
                         operator: str,
                         folder: str) -> None:
    """
    Create holiday json for the selected operator.
    """
    holidays = siri_client.holidays(operator)
    file_path = os.path.join(folder, 'holidays.json')
    with open(file_path, 'w') as outfile:
        json.dump(holidays, outfile, indent=4)


def create_stop_monitoring_json(siri_client: siri_transit_api_client.siri_client.SiriClient,
                                operator: str,
                                stop_code: str,
                                folder: str) -> None:
    """
    Create a stop monitoring json for the given operator and stop code.
    """
    stop_monitoring = siri_client.stop_monitoring(operator, stop_code=stop_code)
    file_path = os.path.join(folder, 'stop_monitoring.json')
    with open(file_path, 'w') as outfile:
        json.dump(stop_monitoring, outfile, indent=4)


def create_stop_places_json(siri_client: siri_transit_api_client.siri_client.SiriClient,
                            operator: str,
                            stop_code: str,
                            new_time_dt: dt.datetime,
                            folder: str
                            ) -> None:
    """
    Create the stop places code for the given operator and stop code.
    """
    stop_places = siri_client.stop_places(operator, stop_id=stop_code)
    stop_places['Siri']['ServiceDelivery']['ResponseTimestamp'] = new_time_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    stop_places['Siri']['ServiceDelivery']['DataObjectDelivery']['ResponseTimestamp'] = new_time_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    file_path = os.path.join(folder, 'stop_places.json')
    with open(file_path, 'w') as outfile:
        json.dump(stop_places, outfile, indent=4)


def create_timetable_json(siri_client: siri_transit_api_client.siri_client.SiriClient,
                          operator: str,
                          line_id: str,
                          folder: str) -> None:
    """
    Create timetable json for the given operator and line id.
    """
    timetable = siri_client.timetable(operator, line_id=line_id)
    file_path = os.path.join(folder, 'timetable.json')
    with open(file_path, 'w') as outfile:
        json.dump(timetable, outfile, indent=4)


def parse_time_str(time_str: typing.Optional[str] = None):
    """
    Parses the time string and returns datetime object if time string is not none. If none, returns none.
    """
    if time_str is None:
        return None
    else:
        return dateutil.parser.isoparse(time_str).replace(tzinfo=None)


def modify_timetable(timetable: dict,
                     name: str,
                     cur_time: dt.datetime,
                     scheduled_arrival: dt.timedelta) -> dict:
    """
    Creates a modified timetable entry by changing the name, aimed arrival time and aimed departure time.
    """
    time = cur_time + scheduled_arrival
    timetable['TargetedVehicleJourney']['DatedVehicleJourneyRef'] = name
    timetable['TargetedVehicleJourney']['TargetedCall']['AimedArrivalTime'] = time.isoformat()
    timetable['TargetedVehicleJourney']['TargetedCall']['AimedDepartureTime'] = time.isoformat()
    return timetable


def modify_vehicle(vehicle_in: dict,
                   name: str,
                   stop_code: str,
                   new_time_dt: dt.datetime,
                   scheduled_arrival: dt.timedelta,
                   estimated_arrival: dt.timedelta) -> dict:
    """
    Creates a modified vehicle by changing the name and updating future stops
    """
    vehicle_in['MonitoredVehicleJourney']['FramedVehicleJourneyRef']['DatedVehicleJourneyRef'] = name
    onward_call_df = pd.DataFrame(vehicle_in['MonitoredVehicleJourney']['OnwardCalls']['OnwardCall'])
    onward_call_df = convert_onward_calls_to_deltas(onward_call_df, stop_code)
    df_onward_call, next_stop = modify_onward_calls(onward_call_df, new_time_dt, scheduled_arrival, estimated_arrival)
    vehicle_in['MonitoredVehicleJourney']['OnwardCalls']['OnwardCall'] = df_onward_call.to_dict('records')
    vehicle_in['MonitoredVehicleJourney']['MonitoredCall'] = next_stop.to_dict()
    vehicle_in['RecordedAtTime'] = new_time_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    vehicle_in['MonitoredVehicleJourney']['FramedVehicleJourneyRef']['DataFrameRef'] = new_time_dt.strftime('%Y-%m-%d')
    return vehicle_in


def modify_onward_calls(df: pd.DataFrame,
                        cur_time: dt.datetime,
                        scheduled_arrival: dt.timedelta,
                        estimated_arrival: dt.timedelta) -> tuple[pd.DataFrame, pd.Series]:
    """
    Modify the onward calls by shifting schedule. Change the aimed arrival time to simulate an early or late bus.
    """
    # modify the onward calls
    df['AimedArrivalTimeObj'] = df['AimedArrivalTime'] + cur_time + scheduled_arrival
    df['ExpectedArrivalTimeObj'] = df['ExpectedArrivalTime'] + cur_time + estimated_arrival
    df['AimedDepartureTimeObj'] = df['AimedDepartureTime'] + cur_time + scheduled_arrival
    # create iso format
    df = convert_time_iso_format(df)
    # select the next stop
    next_stop = df[df['ExpectedArrivalTimeObj'] >= cur_time].iloc[0]
    next_stop['VehicleLocationAtStop'] = ''
    if next_stop['ExpectedArrivalTime'] == cur_time:
        next_stop['VehicleAtStop'] = True
    else:
        next_stop['VehicleAtStop'] = ''
    next_stop = next_stop.drop(['AimedArrivalTimeObj', 'ExpectedArrivalTimeObj', 'AimedDepartureTimeObj'])
    # select the upcoming stops
    upcoming_stops = df[df['ExpectedArrivalTimeObj'] >= cur_time].iloc[1:]
    upcoming_stops = upcoming_stops.drop(['AimedArrivalTimeObj', 'ExpectedArrivalTimeObj', 'AimedDepartureTimeObj'],
                                         axis=1)
    return upcoming_stops, next_stop


def convert_time_iso_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert time columns to iso format.
    """
    df['AimedArrivalTime'] = df['AimedArrivalTimeObj'].map(
        lambda x: x.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    df['ExpectedArrivalTime'] = df['ExpectedArrivalTimeObj'].map(
        lambda x: x.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    df['AimedDepartureTime'] = df['AimedDepartureTimeObj'].map(
        lambda x: x.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    return df


def convert_to_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert the time columns to date time objects.
    """
    df['AimedArrivalTime'] = pd.to_datetime(df['AimedArrivalTime'])
    df['ExpectedArrivalTime'] = pd.to_datetime(df['ExpectedArrivalTime'])
    df['AimedDepartureTime'] = pd.to_datetime(df['AimedDepartureTime'])
    return df


def create_stop_dict(df: pd.DataFrame, stop_code: str) -> dict:
    """
    Return record for the desired stop.
    """
    df = convert_to_datetime(df)
    # select the call at the stop and convert to dict
    stop = df[df['StopPointRef'] == stop_code]
    stop_dict = stop.to_dict('records')[0]
    return stop_dict


def convert_onward_calls_to_deltas(df: pd.DataFrame, stop_code: str) -> pd.DataFrame:
    """
    Convert onward calls to time deltas.
    """
    df = convert_to_datetime(df)
    stop_dict = create_stop_dict(df, stop_code)
    # create time deltas by subtracting stop code row
    df['AimedArrivalTime'] = df['AimedArrivalTime'] - stop_dict['AimedArrivalTime']
    df['ExpectedArrivalTime'] = df['ExpectedArrivalTime'] - stop_dict[
        'ExpectedArrivalTime']
    df['AimedDepartureTime'] = df['AimedDepartureTime'] - stop_dict[
        'AimedDepartureTime']
    return df


def determine_vehicles_that_stop(timetable_dict: dict) -> dict:
    """
    Determine vehicles that stop at the desired stop
    """
    vehicles = {}
    for vehicle in timetable_dict['Siri']['ServiceDelivery']['StopTimetableDelivery']['TimetabledStopVisit']:
        vehicles[vehicle['TargetedVehicleJourney']['DatedVehicleJourneyRef']] = vehicle
    return vehicles


def determine_length_of_onward_calls(vehicle_dict: dict, stopping_vehicles: dict) -> pd.DataFrame:
    """
    Determine the length of onward calls for all the vehicles
    """
    vehicles = []
    for vehicle in vehicle_dict['Siri']['ServiceDelivery']['VehicleMonitoringDelivery']['VehicleActivity']:
        vehicle_journey_ref = vehicle['MonitoredVehicleJourney']['FramedVehicleJourneyRef']['DatedVehicleJourneyRef']

        if vehicle_journey_ref in stopping_vehicles.keys():
            if 'OnwardCalls' in vehicle['MonitoredVehicleJourney']:
                len_onward_calls = len(vehicle['MonitoredVehicleJourney']['OnwardCalls']['OnwardCall'])
            else:
                len_onward_calls = 0

            vehicles.append(
                {'DatedVehicleJourneyRef': vehicle_journey_ref,
                 'len_onward_calls': len_onward_calls,
                 'vehicle_dict': vehicle}
            )
    return pd.DataFrame(vehicles)


def select_vehicle_example(df: pd.DataFrame) -> dict:
    """
    Select vehicle monitoring example
    """
    selected_vehicle = df[df['len_onward_calls'] == df['len_onward_calls'].max()]
    return selected_vehicle['vehicle_dict'].values[0]


def select_timetable_example(vehicle: dict, stopping_vehicles: dict) -> dict:
    """
    Select timetable example
    """
    selected_vehicle_id = vehicle['MonitoredVehicleJourney']['FramedVehicleJourneyRef'][
        'DatedVehicleJourneyRef']
    return stopping_vehicles[selected_vehicle_id]


def write_stop_timetable_json(stop_timetable_dict: dict,
                              folder: str) -> None:
    """
    Write the stop timetable json.
    """
    file_path = os.path.join(folder, 'stop_timetable_modified.json')
    with open(file_path, 'w') as outfile:
        json.dump(stop_timetable_dict, outfile)


def write_vehicle_monitoring_json(vehicle_monitoring_dict: dict,
                                  folder: str):
    """
    Write the vehicle monitoring json.
    """
    file_path = os.path.join(folder, 'vehicle_monitoring_modified.json')
    with open(file_path, 'w') as outfile:
        json.dump(vehicle_monitoring_dict, outfile)


def create_modified_vehicles_timetable_json(siri_client: siri_transit_api_client.siri_client.SiriClient,
                                            operator: str,
                                            stop_code: str,
                                            new_time_dt: dt.datetime,
                                            folder: str
                                            ) -> None:
    """
    Modify the vehicles and timetable jsons to create specific test cases.
    """
    stop_timetable_dict = siri_client.stop_timetable(operator, stop_code)
    vehicle_monitoring_dict = siri_client.vehicle_monitoring(operator)
    # current_time = dt.datetime.fromisoformat(stop_timetable_dict['Siri']['ServiceDelivery']['ResponseTimestamp'])

    vehicles_that_stop = determine_vehicles_that_stop(stop_timetable_dict)
    vehicle_df = determine_length_of_onward_calls(vehicle_monitoring_dict, vehicles_that_stop)
    vehicle_monitoring_example = select_vehicle_example(vehicle_df)
    stop_timetable_example = select_timetable_example(vehicle_monitoring_example, vehicles_that_stop)

    vehicles = []
    for vehicle in vehicle_test_cases:
        if vehicle['EstimatedArrival'] is not None:
            vehicles.append(modify_vehicle(copy.deepcopy(vehicle_monitoring_example),
                                           vehicle['Name'],
                                           stop_code,
                                           new_time_dt,
                                           vehicle['ScheduledArrival'],
                                           vehicle['EstimatedArrival']))

    vehicle_monitoring_dict['Siri']['ServiceDelivery']['VehicleMonitoringDelivery']['VehicleActivity'] = vehicles
    vehicle_monitoring_dict['Siri']['ServiceDelivery']['ResponseTimestamp'] = new_time_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    vehicle_monitoring_dict['Siri']['ServiceDelivery'][
        'VehicleMonitoringDelivery']['ResponseTimestamp'] = new_time_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    write_vehicle_monitoring_json(vehicle_monitoring_dict, folder)
    timetables = []
    for vehicle in vehicle_test_cases:
        timetables.append(modify_timetable(copy.deepcopy(stop_timetable_example),
                                           vehicle['Name'],
                                           new_time_dt,
                                           vehicle['ScheduledArrival']))
    stop_timetable_dict['Siri']['ServiceDelivery']['StopTimetableDelivery']['TimetabledStopVisit'] = timetables
    stop_timetable_dict['Siri']['ServiceDelivery']['ResponseTimestamp'] = new_time_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    stop_timetable_dict['Siri']['ServiceDelivery']['StopTimetableDelivery'][
        'ResponseTimestamp'] = new_time_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    write_stop_timetable_json(stop_timetable_dict, folder)


def select_example_monitored_stops(input_dict: dict) -> (dict, dict, dict):
    """
    Select example monitored vehicles: a vehicle that goes to two stops and a vehicle on another line.
    """
    monitored_stop_visits = input_dict['ServiceDelivery']['StopMonitoringDelivery']['MonitoredStopVisit']
    flattened_stop_monitors = []
    for monitored_stop_visit in monitored_stop_visits:
        stop_id = monitored_stop_visit["MonitoredVehicleJourney"]["MonitoredCall"]["StopPointRef"]
        line_id = monitored_stop_visit["MonitoredVehicleJourney"]["LineRef"]
        vehicle_journey_ref = monitored_stop_visit["MonitoredVehicleJourney"]["FramedVehicleJourneyRef"][
            "DatedVehicleJourneyRef"]
        if stop_id in selected_stops and line_id in selected_lines:
            flattened_stop_monitors.append({
                "stop_id": stop_id,
                "line_id": line_id,
                "vehicle_journey_ref": vehicle_journey_ref,
                "monitored_stop_visit": monitored_stop_visit
            })

    stop_monitor_df = pd.DataFrame(flattened_stop_monitors)
    vehicle_visit_two_stops = stop_monitor_df['vehicle_journey_ref'].value_counts().index[0]
    vehicle_visit_two_stops_stop_1 = stop_monitor_df[
        (stop_monitor_df['vehicle_journey_ref'] == vehicle_visit_two_stops) &
        (stop_monitor_df['stop_id'] == selected_stops[0])
         ].iloc[0]['monitored_stop_visit']
    vehicle_visit_two_stops_stop_2 = stop_monitor_df[
        (stop_monitor_df['vehicle_journey_ref'] == vehicle_visit_two_stops) &
        (stop_monitor_df['stop_id'] == selected_stops[1])
          ].iloc[0]['monitored_stop_visit']
    line_id_vehicle_visit_two_stops = stop_monitor_df[stop_monitor_df['vehicle_journey_ref'] ==
                                                      vehicle_visit_two_stops].iloc[0]['line_id']
    vehicle_other_line = stop_monitor_df[
        (stop_monitor_df['line_id'] != line_id_vehicle_visit_two_stops) &
        (stop_monitor_df['stop_id'] == selected_stops[0])].iloc[0]['monitored_stop_visit']
    return vehicle_visit_two_stops_stop_1, vehicle_visit_two_stops_stop_2, vehicle_other_line


def modify_monitored_stop(monitored_stop_dict: dict,
                          new_time_dt: dt.datetime,
                          vehicle_modification_dict: dict) -> dict:
    """
    Modify the monitored stop by shifting the time.
    """
    monitored_stop_dict['RecordedAtTime'] = new_time_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    monitored_stop_dict['MonitoredVehicleJourney']['FramedVehicleJourneyRef']['DataFrameRef'] = (
        new_time_dt.strftime('%Y-%m-%d'))
    monitored_stop_dict['MonitoredVehicleJourney']['FramedVehicleJourneyRef']['DatedVehicleJourneyRef'] = (
        vehicle_modification_dict['Name']
    )
    aimed_arrival_time = new_time_dt + vehicle_modification_dict['ScheduledArrival']
    expected_arrival_time = new_time_dt + vehicle_modification_dict['EstimatedArrival']
    aimed_departure_time = aimed_arrival_time
    monitored_stop_dict['MonitoredVehicleJourney']['MonitoredCall'][
        'AimedArrivalTime'] = aimed_arrival_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    monitored_stop_dict['MonitoredVehicleJourney']['MonitoredCall'][
        'ExpectedArrivalTime'] = expected_arrival_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    monitored_stop_dict['MonitoredVehicleJourney']['MonitoredCall'][
        'AimedDepartureTime'] = aimed_departure_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    if vehicle_modification_dict['EstimatedArrival'] == dt.timedelta(0):
        monitored_stop_dict['MonitoredVehicleJourney']['MonitoredCall']['VehicleAtStop'] = True
    return monitored_stop_dict


def write_stop_monitoring_json(stop_monitoring_dict: dict,
                               folder: str) -> None:
    """
    Write the stop monitoring json.
    """
    file_path = os.path.join(folder, "stop_monitoring_modified.json")
    with open(file_path, "w") as outfile:
        json.dump(stop_monitoring_dict, outfile)


def create_modified_stop_monitoring_json(siri_client: siri_transit_api_client.siri_client.SiriClient,
                                         operator: str,
                                         folder: str,
                                         new_time_dt: dt.datetime) -> None:
    """
    Create the stop monitoring json.
    """
    stop_monitoring_dict = siri_client.stop_monitoring(operator)
    (vehicle_visit_two_stops_stop_1, vehicle_visit_two_stops_stop_2,
     vehicle_other_line) = select_example_monitored_stops(stop_monitoring_dict)
    modified_vehicle_list = [
        modify_monitored_stop(copy.deepcopy(vehicle_visit_two_stops_stop_1), new_time_dt,
                              stop_monitoring_test_cases[0]),
        modify_monitored_stop(copy.deepcopy(vehicle_visit_two_stops_stop_2), new_time_dt,
                              stop_monitoring_test_cases[1]),
        modify_monitored_stop(copy.deepcopy(vehicle_other_line), new_time_dt, stop_monitoring_test_cases[2]),
        modify_monitored_stop(copy.deepcopy(vehicle_other_line), new_time_dt, stop_monitoring_test_cases[3]),
        modify_monitored_stop(copy.deepcopy(vehicle_other_line), new_time_dt, stop_monitoring_test_cases[4])
    ]
    stop_monitoring_dict['ServiceDelivery']['StopMonitoringDelivery']['MonitoredStopVisit'] = modified_vehicle_list
    stop_monitoring_dict['ServiceDelivery']['ResponseTimestamp'] = new_time_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    stop_monitoring_dict['ServiceDelivery']['StopMonitoringDelivery']['ResponseTimestamp'] = (
        new_time_dt.strftime('%Y-%m-%dT%H:%M:%SZ'))

    write_stop_monitoring_json(stop_monitoring_dict, folder)

def main():
    # import the configuration file which has the api keys
    config = configparser.ConfigParser()
    config.read('./key_api.ini')
    transit_api_key = config['keys']['Transit511Key']
    siri_base_url = config['keys']['base_url']

    client = siri_transit_api_client.SiriClient(api_key=transit_api_key, base_url=siri_base_url)
    create_operator_json(client, selected_operators, json_folder)
    create_lines_json(client, selected_operator, selected_lines, json_folder)
    create_stops_json(client, selected_operator, selected_stops, new_time, json_folder)
    create_patterns_json(client, selected_operator, selected_line, json_folder)
    create_vehicle_monitoring_json(client, selected_operator, json_folder)
    create_stop_timetable_json(client, selected_operator, selected_stop, json_folder)
    create_holidays_json(client, selected_operator, json_folder)
    create_stop_monitoring_json(client, selected_operator, selected_stop, json_folder)
    create_stop_places_json(client, selected_operator, selected_stop, new_time, json_folder)
    create_timetable_json(client, selected_operator, selected_line, json_folder)
    create_modified_vehicles_timetable_json(client, selected_operator, selected_stop, new_time, json_folder)
    create_modified_stop_monitoring_json(client, selected_operator, json_folder, new_time)


if __name__ == "__main__":
    main()
