"""Data models."""
from transit_notification import db


class Operators(db.Model):
    operator_id = db.Column(db.String(2), primary_key=True)
    operator_name = db.Column(db.String(100), nullable=False)
    operator_monitored = db.Column(db.Boolean, nullable=False)
    lines_updated = db.Column(db.DateTime)
    stops_updated = db.Column(db.DateTime)
    vehicle_monitoring_updated = db.Column(db.DateTime)
    lines = db.relationship('Lines', backref='operator', lazy=True)
    stops = db.relationship('Stops', backref='operator', lazy=True)

    def __init__(self, operator_id, operator_name, operator_monitored):
        self.operator_id = operator_id
        self.operator_name = operator_name
        self.operator_monitored = operator_monitored

    def __repr__(self):
        return f"Id : {self.operator_id}, Name: {self.operator_name}, Monitored: {self.operator_monitored}, " \
               f"Lines Updated: {self.lines_updated}, "f"Stops Updated: {self.stops_updated}, " \
               f"Vehicle Monitoring Updated: {self.vehicle_monitoring_updated}"


class Lines(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operators.operator_id"), nullable=False, primary_key=True)
    line_id = db.Column(db.String(10), primary_key=True)
    line_name = db.Column(db.String(100), nullable=False)
    monitored = db.Column(db.Boolean, nullable=False)
    sort_index = db.Column(db.Float, nullable=False)
    direction_0_id = db.Column(db.String(10))
    direction_0_name = db.Column(db.String(100))
    direction_1_id = db.Column(db.String(10))
    direction_1_name = db.Column(db.String(100))

    def __init__(self, line_id, operator_id, line_name, line_monitored, sort_index):
        self.line_id = line_id
        self.operator_id = operator_id
        self.line_name = line_name
        self.line_monitored = line_monitored
        self.sort_index = sort_index

    def __repr__(self):
        return f"Id: {self.line_id}, Name: {self.line_name}, Monitored: {self.line_monitored}, " \
               f"Direction 0 Id: {self.direction_0_id}, Direction 0 Name: {self.direction_0_name}, " \
               f"Direction 1 Id: {self.direction_1_id}, Direction 0 Name: {self.direction_1_name}"


class Stops(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operators.operator_id"), nullable=False, primary_key=True)
    stop_id = db.Column(db.String(10), primary_key=True)
    stop_name = db.Column(db.String(100), nullable=False)
    stop_longitude = db.Column(db.Float, nullable=False)
    stop_latitude = db.Column(db.Float, nullable=False)

    def __init__(self, operator_id, stop_id, stop_name, stop_longitude, stop_latitude):
        self.operator_id = operator_id
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.stop_longitude = stop_longitude
        self.stop_latitude = stop_latitude

    def __repr__(self):
        return f"Id : {self.stop_id}, Name: {self.stop_name}, Longitude: {self.stop_longitude}, " \
               f"Latitude: {self.stop_latitude}"


class Vehicles(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operators.operator_id"), nullable=False, primary_key=True)
    vehicle_journey_ref = db.Column(db.String(100), nullable=False, primary_key=True)
    dataframe_ref = db.Column(db.String(100), nullable=False, primary_key=True)
    line_id = db.Column(db.String(10), db.ForeignKey("lines.line_id"), nullable=False)
    vehicle_direction = db.Column(db.String(2), nullable=False)
    vehicle_longitude = db.Column(db.Float, nullable=False)
    vehicle_latitude = db.Column(db.Float, nullable=False)

    def __init__(self,
                 operator_id,
                 vehicle_journey_ref,
                 dataframe_ref,
                 line_id,
                 vehicle_direction,
                 vehicle_longitude,
                 vehicle_latitude):
        self.operator_id = operator_id
        self.vehicle_journey_ref = vehicle_journey_ref
        self.dataframe_ref = dataframe_ref
        self.line_id = line_id
        self.vehicle_direction = vehicle_direction
        self.vehicle_longitude = vehicle_longitude
        self.vehicle_latitude = vehicle_latitude

    def __repr__(self):
        return f"Vehicle : {self.vehicle_journey_ref}, DateFrameRef: {self.dataframe_ref}, " \
               f"Direction: {self.vehicle_direction}, Longitude: {self.vehicle_longitude}, " \
               f"Latitude: {self.vehicle_latitude}"

    def contains_none(self):
        return None in self.__dict__.values()


class Patterns(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operators.operator_id"), nullable=False, primary_key=True)
    line_id = db.Column(db.String(10), db.ForeignKey("lines.line_id"), nullable=False, primary_key=True)
    pattern_id = db.Column(db.Float, nullable=False, primary_key=True)
    pattern_name = db.Column(db.String(100), nullable=False)
    pattern_direction = db.Column(db.String(10), nullable=False)
    pattern_trip_count = db.Column(db.Float, nullable=False)

    def __init__(self, operator_id, line_id, pattern_id, pattern_name, pattern_direction, pattern_trip_count):
        self.operator_id = operator_id
        self.line_id = line_id
        self.pattern_id = pattern_id
        self.pattern_name = pattern_name
        self.pattern_direction = pattern_direction
        self.pattern_trip_count = pattern_trip_count


class StopPatterns(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operators.operator_id"), nullable=False, primary_key=True)
    pattern_id = db.Column(db.Float, db.ForeignKey("patterns.pattern_id"), nullable=False, primary_key=True)
    stop_order = db.Column(db.Float, nullable=False, primary_key=True)
    stop_id = db.Column(db.Float, db.ForeignKey("stops.stop_id"), nullable=False)

    def __init__(self, operator_id, pattern_id, stop_order, stop_id):
        self.operator_id = operator_id
        self.pattern_id = pattern_id
        self.stop_order = stop_order
        self.stop_id = stop_id


class OnwardCalls(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operators.operator_id"), nullable=False, primary_key=True)
    vehicle_journey_ref = db.Column(db.String(100), nullable=False, primary_key=True)
    dataframe_ref = db.Column(db.String(100), nullable=False, primary_key=True)
    stop_id = db.Column(db.Float, db.ForeignKey("stops.stop_id"), nullable=False)
    aimed_arrival = db.Column(db.DateTime)
    expected_arrival = db.Column(db.DateTime)
    aimed_departure = db.Column(db.DateTime)
    expected_departure = db.Column(db.DateTime)
