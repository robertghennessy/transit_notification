"""Data models."""
from transit_notification import db


class Operators(db.Model):
    id = db.Column(db.String(2), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    monitored = db.Column(db.Boolean, nullable=False)
    lines_updated = db.Column(db.DateTime)
    stops_updated = db.Column(db.DateTime)
    vehicle_monitoring_updated = db.Column(db.DateTime)
    lines = db.relationship('Lines', backref='operator', lazy=True)
    stops = db.relationship('Stops', backref='operator', lazy=True)

    def __repr__(self):
        return f"Id : {self.id}, Name: {self.name}, Monitored: {self.monitored}, " \
               f"Lines Updated: {self.lines_updated}, "f"Stops Updated: {self.stops_updated}, " \
               f"Vehicle Monitoring Updated: {self.vehicle_monitoring_updated}"


class Lines(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operators.id"), nullable=False, primary_key=True)
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    monitored = db.Column(db.Boolean, nullable=False)
    sort_index = db.Column(db.Float, nullable=False)
    direction_1 = db.Column(db.String(10))
    direction_2 = db.Column(db.String(10))

    def __repr__(self):
        return f"Id : {self.id}, Name: {self.name}, Monitored: {self.monitored}"


class Stops(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operators.id"), nullable=False, primary_key=True)
    id = db.Column(db.String(2), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"Id : {self.id}, Name: {self.name}, Longitude: {self.ongitude}, Latitude: {self.latitude}"


class Vehicles(db.Model):
    operator_id = db.Column(db.String(2), db.ForeignKey("operators.id"), nullable=False, primary_key=True)
    vehicle_journey_ref = db.Column(db.String(100), nullable=False, primary_key=True)
    dataframe_ref = db.Column(db.String(100), nullable=False, primary_key=True)
    line_id = db.Column(db.String(10), db.ForeignKey("lines.id"), nullable=False)
    direction = db.Column(db.String(2), nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"Vehicle : {self.vehicle_journey_ref}, DateFrameRef: {self.dataframe_ref}, " \
               f"Direction: {self.direction}, Longitude: {self.longitude}, Latitude: {self.latitude}"
