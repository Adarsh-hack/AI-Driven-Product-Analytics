from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models.project import Project

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    """Main dashboard page - shows summary of all projects"""
    # Get all projects for the current user
    projects = Project.query.filter_by(user_id=current_user.id).all()
    
    # If user has no projects, redirect to project creation
    if not projects:
        return render_template('dashboard/empty.html')
    
    # Return the dashboard with projects
    return render_template('dashboard/index.html', projects=projects)