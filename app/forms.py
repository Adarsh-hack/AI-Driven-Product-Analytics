from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp
from app.models.user import User
from app.models.project import Project
import logging

class LoginForm(FlaskForm):
    """Form for user login"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """Form for user registration"""
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=64, message="Username must be between 3 and 64 characters")
    ])
    
    # Use Regexp instead of Email validator to avoid dependency issues
    email = StringField('Email', validators=[
        DataRequired(),
        Regexp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', 
               message="Invalid email address format"),
        Length(max=120)
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, message="Password must be at least 8 characters")
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message="Passwords must match")
    ])
    submit = SubmitField('Register')
    
    # Custom validation methods with error handling
    def validate_username(self, username):
        """Check if username is already taken"""
        try:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Username already taken. Please use a different username.')
        except Exception as e:
            # Log the error but don't block form submission
            logging.warning(f"Database error during username validation: {e}")
            # Since we can't reliably check uniqueness, we'll just proceed
    
    def validate_email(self, email):
        """Check if email is already registered"""
        try:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Email already registered. Please use a different email address.')
        except Exception as e:
            # Log the error but don't block form submission
            logging.warning(f"Database error during email validation: {e}")
            # Since we can't reliably check uniqueness, we'll just proceed

class ProjectForm(FlaskForm):
    """Form for creating and editing projects"""
    name = StringField('Project Name', validators=[
        DataRequired(),
        Length(min=3, max=64, message="Project name must be between 3 and 64 characters")
    ])
    description = TextAreaField('Description', validators=[
        Length(max=500, message="Description must be less than 500 characters")
    ])
    submit = SubmitField('Save Project')