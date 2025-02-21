from datetime import datetime
from app import db

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    appointments = db.relationship('Appointment', backref='patient', lazy=True)

class Technician(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    availability = db.relationship('Availability', backref='technician', lazy=True)
    appointments = db.relationship('Appointment', backref='technician', lazy=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('technician.id'), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='scheduled')
    notes = db.Column(db.Text)

class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    technician_id = db.Column(db.Integer, db.ForeignKey('technician.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0-6 for Monday-Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)