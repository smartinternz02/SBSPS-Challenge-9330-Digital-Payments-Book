from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField
from wtforms.validators import InputRequired, Length, Email, EqualTo
from functools import wraps
from flask import session, redirect
from cs50 import SQL

db = SQL('sqlite:///amends.db')


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[InputRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class EditProfileForm(FlaskForm):
    username = StringField('Username',
                           validators=[InputRequired(), Length(min=2, max=20)])
    budget = IntegerField('Budget', validators=[InputRequired()])
    submit = SubmitField('Save Changes')


class AnalysisForm(FlaskForm):
    first_month = SelectField('Choose a Month', choices=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], validate_choice=True, validators=[InputRequired()])
    second_month = SelectField('Choose a Month', choices=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], validate_choice=True, validators=[InputRequired()])
    submit = SubmitField('Compare')


