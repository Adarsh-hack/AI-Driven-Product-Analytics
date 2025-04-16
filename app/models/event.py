from datetime import datetime
from sqlalchemy.types import JSON, TypeDecorator, TEXT
import json
from app.models import db

# Custom JSON type for SQLite compatibility
class JSONType(TypeDecorator):
    impl = TEXT
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value
        
    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

# Choose appropriate JSON type based on dialect
SQLAlchemyJSONType = JSON().with_variant(JSONType(), 'sqlite')

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    event_name = db.Column(db.String(64), nullable=False, index=True)
    # Store properties as JSON - compatible with both SQLite and PostgreSQL
    properties = db.Column(SQLAlchemyJSONType)
    # External user identifier from the tracked application (not our User model)
    user_id = db.Column(db.String(64), nullable=True, index=True)
    # For anonymous users without a user_id
    anonymous_id = db.Column(db.String(64), nullable=True, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Event {self.event_name} for Project {self.project_id}>'