from flask import Blueprint, request, jsonify, current_app
from app.models import db
from app.models.event import Event
from app.models.project import Project
from datetime import datetime
import json

bp = Blueprint('events', __name__, url_prefix='/api')

@bp.route('/events', methods=['POST', 'OPTIONS'])
def capture_event():
    """
    API endpoint for capturing events from client tracking snippet
    Supports CORS for mobile web apps
    """
    # Handle preflight OPTIONS request for CORS
    if request.method == 'OPTIONS':
        response = current_app.make_default_options_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response
    
    # Check for proper JSON content
    if not request.is_json:
        response = jsonify({
            "status": "error",
            "message": "Content-Type must be application/json"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    
    # Get the JSON data
    data = request.json
    
    # Validate required fields
    required_fields = ['project_id', 'event_name']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        response = jsonify({
            "status": "error",
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    
    # Find project by tracking_id
    project = Project.query.filter_by(tracking_id=data['project_id']).first()
    
    if not project:
        response = jsonify({
            "status": "error",
            "message": "Invalid project ID"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    
    # Process timestamp
    timestamp = datetime.utcnow()
    if 'timestamp' in data and data['timestamp']:
        try:
            timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except (ValueError, TypeError):
            # If timestamp is invalid, use current time
            current_app.logger.warning(f"Invalid timestamp format: {data.get('timestamp')}")
    
    # Create new event
    event = Event(
        project_id=project.id,
        event_name=data['event_name'],
        properties=data.get('properties', {}),
        user_id=data.get('user_id'),
        anonymous_id=data.get('anonymous_id'),
        timestamp=timestamp
    )
    
    # Save to database
    try:
        db.session.add(event)
        db.session.commit()
        response = jsonify({
            "status": "success",
            "message": "Event recorded successfully",
            "event_id": event.id
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving event: {str(e)}")
        response = jsonify({
            "status": "error",
            "message": "Failed to record event"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@bp.route('/events/test', methods=['GET', 'POST', 'OPTIONS'])
def test_endpoint():
    """
    Simple endpoint to test API connectivity
    Supports CORS for mobile web apps
    """
    # Handle preflight OPTIONS request for CORS
    if request.method == 'OPTIONS':
        response = current_app.make_default_options_response()
    else:
        response = jsonify({
            "status": "success",
            "message": "API is working correctly",
            "timestamp": datetime.utcnow().isoformat(),
            "cors_enabled": True
        })
    
    # Add CORS headers
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    
    return response, 200