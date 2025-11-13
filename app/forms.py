from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, DateField, TimeField, SubmitField, IntegerField, FloatField, SelectField


from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange



class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class UserCreateForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    role = SelectField("Role", choices=[("Admin","Admin"),("Sales","Sales"),("Manager","Manager"),("Accountant","Accountant")])
    submit = SubmitField("Create")

class FollowUpForm(FlaskForm):
    client_name = StringField("Client Name", validators=[DataRequired()])
    client_phone = StringField("Client Phone", validators=[DataRequired()])
    followup_date = DateField("Follow-up Date", format="%Y-%m-%d", validators=[DataRequired()])
    followup_time = TimeField("Follow-up Time", format="%H:%M", validators=[DataRequired()])
    note = TextAreaField("Note")
    submit = SubmitField("Schedule Follow-up")


class ProductForm(FlaskForm):
    name = StringField("Product Name", validators=[DataRequired()])
    details = TextAreaField("Details")
    website_price = FloatField("Website Price", validators=[NumberRange(min=0)], default=0.0)
    submit = SubmitField("Save Product")

class QuotationForm(FlaskForm):
    client_name = StringField("Client Name", validators=[DataRequired()])
    client_phone = StringField("Client Phone", validators=[DataRequired(), Length(min=10, max=15)])
    product_name = StringField("Product Name", validators=[DataRequired()])
    product_details = TextAreaField("Product Details")
    website_price = FloatField("Website Price", validators=[NumberRange(min=0)], default=0.0)
    submit = SubmitField("Create Quotation")

class InvoiceForm(FlaskForm):
    client_name = StringField("Client Name", validators=[DataRequired()])
    item_name = StringField("Item Name", validators=[DataRequired()])
    item_qty = IntegerField("Quantity", validators=[DataRequired()])
    item_price = FloatField("Price", validators=[DataRequired()])
    tax_percent = FloatField("Tax %", default=0)
    submit = SubmitField("Generate Invoice")

