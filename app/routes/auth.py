from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app.models import db
from app.models.user import User
from app.forms import LoginForm, RegistrationForm

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    # Redirect already logged-in users to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create new user
        user = User(
            username=form.username.data, 
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        # Add user to database
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    # Redirect already logged-in users to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Find user by username
        user = User.query.filter_by(username=form.username.data).first()
        
        # Check if user exists and password is correct
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))
        
        # Log in the user
        login_user(user, remember=form.remember_me.data)
        
        # Redirect to the next page if it exists and is safe
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard.index')
        
        flash('Login successful!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Login', form=form)

@bp.route('/logout')
@login_required
def logout():
    """User logout route"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))