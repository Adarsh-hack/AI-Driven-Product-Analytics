from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import db
from app.models.project import Project
from app.models.event import Event
from app.services.analytics import AnalyticsService, MLInsightService
from app.forms import ProjectForm
import uuid

from app.services.deepseek_insights import DeepSeekMLInsights

bp = Blueprint('project', __name__, url_prefix='/projects')

@bp.route('/')
@login_required
def list():
    """List all projects for the current user"""
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.created_at.desc()).all()
    return render_template('projects/list.html', title='My Projects', projects=projects)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new project"""
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            name=form.name.data,
            description=form.description.data if hasattr(form, 'description') else None,
            user_id=current_user.id,
            tracking_id=str(uuid.uuid4())
        )
        db.session.add(project)
        db.session.commit()
        flash('Project created successfully!', 'success')
        return redirect(url_for('project.detail', id=project.id))
    
    return render_template('projects/create.html', title='Create Project', form=form)

@bp.route('/<int:id>')
@login_required
def detail(id):
    """Show project details and tracking code"""
    project = Project.query.get_or_404(id)
    
    # Security check - only allow viewing own projects
    if project.user_id != current_user.id:
        abort(403)
    
    # Generate tracking code snippet for the user to copy
    tracking_code = f"""
<!-- Product Analytics Tracking Code -->
<script>
(function(window, document) {{
    // Create analytics object if it doesn't exist
    window.ProductAnalytics = window.ProductAnalytics || {{}};
    
    // Configuration
    var config = {{
        apiEndpoint: '{request.host_url.rstrip("/")}/api/events',
        projectId: '{project.tracking_id}',
        userId: null,
        anonymousId: null
    }};
    
    // Initialize the tracker
    window.ProductAnalytics.init = function(options) {{
        if (options) {{
            config.userId = options.userId || null;
            config.apiEndpoint = options.apiEndpoint || config.apiEndpoint;
        }}
        
        // Generate anonymous ID if not set
        if (!config.anonymousId) {{
            config.anonymousId = generateId();
        }}
        
        console.log('Product Analytics initialized for project:', config.projectId);
    }};
    
    // Track an event
    window.ProductAnalytics.track = function(eventName, properties) {{
        if (!config.projectId) {{
            console.error('Product Analytics not initialized');
            return;
        }}
        
        var eventData = {{
            project_id: config.projectId,
            event_name: eventName,
            properties: properties || {{}},
            user_id: config.userId,
            anonymous_id: config.anonymousId,
            timestamp: new Date().toISOString()
        }};
        
        // Send the event data to the server
        sendEvent(eventData);
    }};
    
    // Helper function to generate ID
    function generateId() {{
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {{
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        }});
    }}
    
    // Helper function to send event data
    function sendEvent(eventData) {{
        var xhr = new XMLHttpRequest();
        xhr.open('POST', config.apiEndpoint, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function() {{
            if (xhr.readyState === 4) {{
                if (xhr.status === 200) {{
                    console.log('Event tracked:', eventData.event_name);
                }} else {{
                    console.error('Failed to track event:', xhr.statusText);
                }}
            }}
        }};
        xhr.send(JSON.stringify(eventData));
    }}
    
    // Initialize automatically
    window.ProductAnalytics.init();
}})(window, document);
</script>
<!-- End Product Analytics Tracking Code -->
    """
    
    # Generate simplified tracking code
    simplified_tracking_code = f"""
<!-- Product Analytics Simplified -->
<script>
(function(w,d,p){{
  w[p]=w[p]||{{}};
  var id='{project.tracking_id}';
  var aid='xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,function(c){{
    var r=Math.random()*16|0,v=c=='x'?r:(r&0x3|0x8);return v.toString(16);
  }});
  
  w[p].track=function(n,p){{
    var x=new XMLHttpRequest();
    x.open('POST','{request.host_url.rstrip("/")}/api/events',true);
    x.setRequestHeader('Content-Type','application/json');
    x.send(JSON.stringify({{
      project_id:id,
      event_name:n,
      properties:p||{{}},
      anonymous_id:aid,
      timestamp:new Date().toISOString()
    }}));
  }};
  
  // Auto-track page view
  w[p].track('page_view',{{url:location.href,title:d.title}});
}})(window,document,'pa');

// Usage: pa.track('button_click', {{id: 'signup-button'}});
</script>
<!-- End Product Analytics -->
    """
    
    # Get recent events for this project (limit to 10)
    recent_events = None
    if hasattr(project, 'events'):
        recent_events = project.events.order_by(db.desc('timestamp')).limit(10).all()
    
    return render_template('projects/detail.html', title=project.name, 
                          project=project, tracking_code=tracking_code, 
                          simplified_tracking_code=simplified_tracking_code,
                          recent_events=recent_events)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a project"""
    project = Project.query.get_or_404(id)
    
    # Security check - only allow editing own projects
    if project.user_id != current_user.id:
        abort(403)
    
    form = ProjectForm(obj=project)
    if form.validate_on_submit():
        form.populate_obj(project)
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('project.detail', id=project.id))
    
    return render_template('projects/edit.html', title=f'Edit {project.name}', form=form, project=project)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a project"""
    project = Project.query.get_or_404(id)
    
    # Security check - only allow deleting own projects
    if project.user_id != current_user.id:
        abort(403)
    
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('project.list'))


@bp.route('/<int:id>/analytics')
@login_required
def analytics(id):
    """Show analytics for a project"""
    project = Project.query.get_or_404(id)
    
    # Security check - only allow viewing own projects
    if project.user_id != current_user.id:
        abort(403)
    
    # Get time period from request args (default: day)
    time_period = request.args.get('time_period', 'day')
    if time_period not in ['day', 'week', 'month']:
        time_period = 'day'
    
    # Get analytics data
    active_users = AnalyticsService.get_active_users(project.id, time_period)
    event_frequency = AnalyticsService.get_event_frequency(project.id, None, time_period)
    top_events = AnalyticsService.get_top_events(project.id)
    user_segments = MLInsightService.get_user_segments(project.id)
    anomalies = MLInsightService.detect_anomalies(project.id, None, time_period)
    
    # Get total events count
    total_events = sum(event_frequency['counts']) if event_frequency['counts'] else 0
    
    # Calculate events per user
    events_per_user = round(total_events / active_users['count'], 1) if active_users['count'] > 0 else 0
    
    return render_template('projects/analytics.html', 
                          title=f"{project.name} Analytics",
                          project=project,
                          time_period=time_period,
                          active_users=active_users,
                          event_frequency=event_frequency,
                          top_events=top_events,
                          user_segments=user_segments,
                          anomalies=anomalies,
                          total_events=total_events,
                          events_per_user=events_per_user)

@bp.route('/<int:id>/connection-test')
@login_required
def connection_test(id):
    """Show connection test page for a project"""
    project = Project.query.get_or_404(id)
    
    # Security check - only allow viewing own projects
    if project.user_id != current_user.id:
        abort(403)
    
    return render_template('projects/connection_test.html', 
                          title='Connection Test',
                          project=project)
    
@bp.route('/<int:id>/ml-insights')
@login_required
def ml_insights(id):
    """Show ML-powered insights for a project"""
    project = Project.query.get_or_404(id)
    
    # Security check - only allow viewing own projects
    if project.user_id != current_user.id:
        abort(403)
    
    # Check if DeepSeek API key is configured
    api_key = DeepSeekMLInsights.get_api_key()
    api_available = api_key is not None
    
    # Set insight mode based on API availability
    if request.args.get('mode') == 'mock' or not api_available:
        # Use mock data if API is not available or mock mode is requested
        behavior_insights = DeepSeekMLInsights.generate_mock_insights()
        product_recommendations = DeepSeekMLInsights.generate_mock_recommendations()
        using_mock = True
    else:
        # Get real insights from DeepSeek API
        behavior_insights = DeepSeekMLInsights.analyze_user_behavior(project.id)
        product_recommendations = DeepSeekMLInsights.get_product_recommendations(project.id)
        using_mock = False
    
    return render_template('projects/ml_insights.html',
                          title=f"{project.name} - AI Insights",
                          project=project,
                          behavior_insights=behavior_insights,
                          product_recommendations=product_recommendations,
                          api_available=api_available,
                          using_mock=using_mock)