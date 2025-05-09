"""Data models."""
from transit_notification import db
from sqlalchemy import ForeignKeyConstraint


class Operator(db.Model):
    operator_id = db.Column(db.String(2), primary_key=True)
    operator_name = db.Column(db.String(100), nullable=False)
    operator_monitored = db.Column(db.Boolean, default=False, nullable=False)
    lines_updated = db.Column(db.DateTime)
    stops_updated = db.Column(db.DateTime)
    patterns_updated = db.Column(db.DateTime)
    vehicle_monitoring_updated = db.Column(db.DateTime)
    stop_monitoring_updated = db.Column(db.DateTime)

    lines = db.relationship('Line', backref='operator', lazy=True)
    patterns = db.relationship('Pattern', backref='operator', lazy=True)
    stops = db.relationship('Stop', backref='operator', lazy=True)
    vehicles = db.relationship('Vehicle', backref='operator', lazy=True)
    stop_patterns = db.relationship('StopPattern', backref='operator', lazy=True)
    onward_calls = db.relationship('OnwardCall', backref='operator', lazy=True)
    stop_timetable = db.relationship('StopTimetable', backref='operator', lazy=True)

    def __repr__(self):
        return f"Operator Id : {self.operator_id}, Name: {self.operator_name}, Monitored: {self.operator_monitored}, " \
               f"Line Updated: {self.lines_updated}, "f"Stop Updated: {self.stops_updated}, " \
               f"Vehicle Monitoring Updated: {self.vehicle_monitoring_updated}"


class Line(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operator.operator_id"), nullable=False, primary_key=True)
    line_id = db.Column(db.String(10), primary_key=True)
    line_name = db.Column(db.String(100), nullable=False)
    line_monitored = db.Column(db.Boolean, nullable=False)
    sort_index = db.Column(db.Integer, nullable=False)
    direction_0_id = db.Column(db.String(10))
    direction_0_name = db.Column(db.String(100))
    direction_1_id = db.Column(db.String(10))
    direction_1_name = db.Column(db.String(100))
    shape_updated = db.Column(db.DateTime)

    patterns = db.relationship('Pattern', backref='line', lazy=True)
    vehicles = db.relationship('Vehicle', backref='line', lazy=True)

    def __init__(self, line_id, operator_id, line_name, line_monitored, sort_index):
        self.line_id = line_id
        self.operator_id = operator_id
        self.line_name = line_name
        self.line_monitored = line_monitored
        self.sort_index = sort_index

    def __repr__(self):
        return f"Line id: {self.line_id}, Name: {self.line_name}, Monitored: {self.line_monitored}, " \
               f"Direction 0 Id: {self.direction_0_id}, Direction 0 Name: {self.direction_0_name}, " \
               f"Direction 1 Id: {self.direction_1_id}, Direction 0 Name: {self.direction_1_name}"


class Pattern(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operator.operator_id"), nullable=False, primary_key=True)
    line_id = db.Column(db.String(10), db.ForeignKey("line.line_id"), nullable=False, primary_key=True)
    pattern_id = db.Column(db.Integer, nullable=False, primary_key=True)
    pattern_name = db.Column(db.String(100), nullable=False)
    pattern_direction = db.Column(db.String(10), nullable=False)
    pattern_trip_count = db.Column(db.Integer, nullable=False)

    stop_patterns = db.relationship('StopPattern', backref='pattern', lazy=True)

    def __init__(self, operator_id, line_id, pattern_id, pattern_name, pattern_direction, pattern_trip_count):
        self.operator_id = operator_id
        self.line_id = line_id
        self.pattern_id = pattern_id
        self.pattern_name = pattern_name
        self.pattern_direction = pattern_direction
        self.pattern_trip_count = pattern_trip_count


class StopPattern(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operator.operator_id"), nullable=False, primary_key=True)
    pattern_id = db.Column(db.Integer, db.ForeignKey("pattern.pattern_id"), nullable=False, primary_key=True)
    stop_id = db.Column(db.String(10), db.ForeignKey("stop.stop_id"), nullable=False)
    stop_order = db.Column(db.Integer, nullable=False, primary_key=True)
    timing_point = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, operator_id, pattern_id, stop_order, stop_id, timing_point):
        self.operator_id = operator_id
        self.pattern_id = pattern_id
        self.stop_order = stop_order
        self.stop_id = stop_id
        self.timing_point = timing_point


class Stop(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operator.operator_id"), nullable=False, primary_key=True)
    stop_id = db.Column(db.String(10), primary_key=True)
    stop_name = db.Column(db.String(100), nullable=False)
    stop_longitude = db.Column(db.Float, nullable=False)
    stop_latitude = db.Column(db.Float, nullable=False)

    stop_timetables = db.relationship('StopTimetable', backref='stop', lazy=True)
    onward_calls = db.relationship('OnwardCall', backref='stop', lazy=True)

    def __init__(self, operator_id, stop_id, stop_name, stop_longitude, stop_latitude):
        self.operator_id = operator_id
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.stop_longitude = stop_longitude
        self.stop_latitude = stop_latitude

    def __repr__(self):
        return f"Stop id : {self.stop_id}, Name: {self.stop_name}, Longitude: {self.stop_longitude}, " \
               f"Latitude: {self.stop_latitude}"


class Vehicle(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operator.operator_id"), nullable=False, primary_key=True)
    line_id = db.Column(db.String(10), db.ForeignKey("line.line_id"), nullable=False)
    vehicle_journey_ref = db.Column(db.String(100), nullable=False, primary_key=True)
    dataframe_ref_date = db.Column(db.Date, nullable=False, primary_key=True)
    vehicle_direction = db.Column(db.String(2), nullable=False)
    vehicle_longitude = db.Column(db.Float, nullable=True)
    vehicle_latitude = db.Column(db.Float, nullable=True)
    vehicle_bearing = db.Column(db.Float, nullable=True)

    onward_calls = db.relationship('OnwardCall', backref='onward_call', lazy=True)
    stop_timetables = db.relationship('StopTimetable', backref='vehicle', lazy=True)

    def __init__(self,
                 operator_id,
                 vehicle_journey_ref,
                 dataframe_ref_date,
                 line_id,
                 vehicle_direction,
                 vehicle_longitude,
                 vehicle_latitude,
                 vehicle_bearing):
        self.operator_id = operator_id
        self.vehicle_journey_ref = vehicle_journey_ref
        self.dataframe_ref_date = dataframe_ref_date
        self.line_id = line_id
        self.vehicle_direction = vehicle_direction
        self.vehicle_longitude = vehicle_longitude
        self.vehicle_latitude = vehicle_latitude
        self.vehicle_bearing = vehicle_bearing

    def __repr__(self):
        return f"Vehicle : {self.vehicle_journey_ref}, DateFrameRef: {self.dataframe_ref_date}, Line: {self.line_id}, " \
               f"Direction: {self.vehicle_direction}, Longitude: {self.vehicle_longitude}, " \
               f"Latitude: {self.vehicle_latitude}, Bearing: {self.vehicle_bearing}"

    def contains_none(self):
        return ((self.operator_id is None) or (self.vehicle_journey_ref is None) or (self.dataframe_ref_date is None) or
                (self.line_id is None) or (self.vehicle_direction is None))


class OnwardCall(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operator.operator_id"), nullable=False, primary_key=True)
    stop_id = db.Column(db.String(10), db.ForeignKey("stop.stop_id"), nullable=False, primary_key=True)
    vehicle_journey_ref = db.Column(db.String(100), nullable=False, primary_key=True)
    dataframe_ref_date = db.Column(db.Date, nullable=False, primary_key=True)
    vehicle_at_stop = db.Column(db.Boolean, default=False, nullable=False)
    aimed_arrival_time_utc = db.Column(db.DateTime)
    expected_arrival_time_utc = db.Column(db.DateTime)
    aimed_departure_time_utc = db.Column(db.DateTime)
    expected_departure_time_utc = db.Column(db.DateTime)
    ForeignKeyConstraint([vehicle_journey_ref, dataframe_ref_date],
                         [Vehicle.vehicle_journey_ref, Vehicle.dataframe_ref_date])

    def __init__(self,
                 operator_id,
                 vehicle_journey_ref,
                 dataframe_ref_date,
                 stop_id,
                 vehicle_at_stop,
                 aimed_arrival_time_utc,
                 expected_arrival_time_utc,
                 aimed_departure_time_utc,
                 expected_departure_time_utc):
        self.operator_id = operator_id
        self.vehicle_journey_ref = vehicle_journey_ref
        self.dataframe_ref_date = dataframe_ref_date
        self.stop_id = stop_id
        self.vehicle_at_stop = vehicle_at_stop
        self.aimed_arrival_time_utc = aimed_arrival_time_utc
        self.expected_arrival_time_utc = expected_arrival_time_utc
        self.aimed_departure_time_utc = aimed_departure_time_utc
        self.expected_departure_time_utc = expected_departure_time_utc

    def __repr__(self):
        return f"Onward Call, Vehicle : {self.vehicle_journey_ref}, Stop id: {self.stop_id} Vehicle at stop: {self.vehicle_at_stop}, " \
                   f"Expected Arrival Time: {self.expected_arrival_time_utc}"


class StopTimetable(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operator.operator_id"), nullable=False, primary_key=True)
    stop_id = db.Column(db.String(10), db.ForeignKey("stop.stop_id"), nullable=False, primary_key=True)
    vehicle_journey_ref = db.Column(db.String(100), nullable=False, primary_key=True)
    aimed_arrival_time_utc = db.Column(db.DateTime)
    aimed_departure_time_utc = db.Column(db.DateTime)
    ForeignKeyConstraint([vehicle_journey_ref],
                         [Vehicle.vehicle_journey_ref])

    def __init__(self, operator_id, vehicle_journey_ref, stop_id, aimed_arrival_time_utc, aimed_departure_time_utc):
        self.operator_id = operator_id
        self.vehicle_journey_ref = vehicle_journey_ref
        self.stop_id = stop_id
        self.aimed_arrival_time_utc = aimed_arrival_time_utc
        self.aimed_departure_time_utc = aimed_departure_time_utc

    def __repr__(self):
        return f"Stop Timetable, Vehicle Journey Ref: {self.vehicle_journey_ref}, Stop ID: {self.stop_id}, " \
                   f"Aimed Arrival Time: {self.aimed_arrival_time_utc}, " \
               f"Aimed Departure Time: {self.aimed_departure_time_utc}"


class Parameter(db.Model):
    name = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.String(100))

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        return f"name: {self.name}, value: {self.value}"


class Shape(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operator.operator_id"), nullable=False, primary_key=True)
    line_id = db.Column(db.Integer, db.ForeignKey("line.line_id"), nullable=False, primary_key=True)
    shape_order = db.Column(db.Integer, nullable=False, primary_key=True)
    shape_longitude = db.Column(db.Float, nullable=False)
    shape_latitude = db.Column(db.Float, nullable=False)

    def __init__(self, operator_id, line_id, shape_order, shape_longitude, shape_latitude):
        self.operator_id = operator_id
        self.line_id = line_id
        self.shape_order = shape_order
        self.shape_longitude = shape_longitude
        self.shape_latitude = shape_latitude

    def __repr__(self):
        return f"Operator id : {self.operator_id}, Line Id: {self.line_id}, Shape Order: {self.shape_order}, Longitude: {self.shape_longitude}, " \
               f"Latitude: {self.shape_latitude}"


