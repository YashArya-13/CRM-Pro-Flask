from . import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import login_manager
from enum import Enum

class RoleEnum(Enum):
    Admin = "Admin"
    Sales = "Sales"
    Manager = "Manager"
    Accountant = "Accountant"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(30), default=RoleEnum.Sales.value)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, needed):
        return self.role == needed or self.role == RoleEnum.Admin.value

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=True)

class FollowUp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    client_phone = db.Column(db.String(15), nullable=False)
    followup_datetime = db.Column(db.DateTime, nullable=False)
    note = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    details = db.Column(db.Text)
    website_price = db.Column(db.Float, default=0.0)

class Quotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(150), nullable=False)
    client_phone = db.Column(db.String(20), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    product_details = db.Column(db.Text)
    website_price = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.Column(db.Text)  # JSON string: list of {"name":..., "qty":..., "price":...}
    tax_percent = db.Column(db.Float, default=0.0)

    def subtotal(self):
        import json
        items = json.loads(self.items or "[]")
        return sum(i["qty"] * i["price"] for i in items)

    def total(self):
        s = self.subtotal()
        return s + s * (self.tax_percent / 100.0)
