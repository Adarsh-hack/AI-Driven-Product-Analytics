from datetime import datetime
import uuid
from app.models import db
from app.models.event import Event

def generate_tracking_id():
    """Generate a unique tracking ID for a project"""
    return str(uuid.uuid4())

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=True)
    tracking_id = db.Column(db.String(36), unique=True, nullable=False, default=generate_tracking_id)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationship to Event - one project can have many events
    events = db.relationship('Event', backref='project', lazy='dynamic', 
                           cascade='all, delete-orphan')
    
    @property
    def event_count(self):
        """Return the total number of events for this project"""
        return self.events.count()
    
    @property
    def active_users_count(self):
        """Return the number of unique user_ids (excluding nulls)"""
        return self.events.filter(Event.user_id.isnot(None)).distinct(Event.user_id).count()
    
    def __repr__(self):
        return f'<Project {self.name}>'