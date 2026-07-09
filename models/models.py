from extensions import db, bcrypt
from flask_login import UserMixin
import unittest

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)  # Store hashed password
    insurance_details = db.Column(db.String(255), nullable=False)
    is_confirmed = db.Column(db.Boolean, default=False)  # Email confirmation status
    city = db.Column(db.String(100), nullable=False)  # City field
    zip_code = db.Column(db.String(20), nullable=False)  # Zip Code field
    address = db.Column(db.String(255), nullable=False)  # Address field

    def __init__(self, full_name, email, password, insurance_details, city, zip_code, address):
        """Initialize User object with hashed password."""
        self.full_name = full_name
        self.email = email
        self.set_password(password)  # Hash the password before storing
        self.insurance_details = insurance_details
        self.city = city
        self.zip_code = zip_code
        self.address = address

    def set_password(self, password):
        """Hash the password before storing it."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')


    def check_password(self, password):
        """Check if a plaintext password matches the stored hashed password."""
        return bcrypt.check_password_hash(self.password_hash, password)
