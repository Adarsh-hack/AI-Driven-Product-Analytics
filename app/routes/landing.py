from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

bp = Blueprint('landing', __name__)

@bp.route('/')
def index():
    """Main landing page for non-authenticated users"""
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    return render_template('landing/index.html')