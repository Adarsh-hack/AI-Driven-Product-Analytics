from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
from collections import defaultdict
import numpy as np
from app.models import db
from app.models.event import Event
from app.models.project import Project

class AnalyticsService:
    @staticmethod
    def get_active_users(project_id, time_period='day'):
        """
        Get count of active users for a project within time period
        """
        # Determine the cutoff date based on time_period
        cutoff = datetime.utcnow()
        if time_period == 'day':
            cutoff = cutoff - timedelta(days=1)
        elif time_period == 'week':
            cutoff = cutoff - timedelta(days=7)
        elif time_period == 'month':
            cutoff = cutoff - timedelta(days=30)
        
        # Count unique user_ids + anonymous_ids
        query = db.session.query(
            func.count(func.distinct(Event.user_id if Event.user_id is not None else Event.anonymous_id))
        ).filter(
            Event.project_id == project_id,
            Event.timestamp >= cutoff
        )
        
        count = query.scalar() or 0
        
        # Get previous period for comparison
        previous_cutoff = cutoff - (cutoff - datetime.utcnow())
        previous_query = db.session.query(
            func.count(func.distinct(Event.user_id if Event.user_id is not None else Event.anonymous_id))
        ).filter(
            Event.project_id == project_id,
            Event.timestamp >= previous_cutoff,
            Event.timestamp < cutoff
        )
        
        previous_count = previous_query.scalar() or 0
        change = count - previous_count
        change_percent = (change / previous_count * 100) if previous_count > 0 else 0
        
        return {
            'count': count,
            'change': change,
            'change_percent': round(change_percent, 1),
            'time_period': time_period
        }
    
    @staticmethod
    def get_event_frequency(project_id, event_name=None, time_period='day'):
        """
        Get frequency of events within time period
        """
        # Determine the cutoff date based on time_period
        cutoff = datetime.utcnow()
        if time_period == 'day':
            cutoff = cutoff - timedelta(days=1)
            group_by = func.strftime('%H', Event.timestamp)
            format_str = '%H:00'
        elif time_period == 'week':
            cutoff = cutoff - timedelta(days=7)
            group_by = func.strftime('%Y-%m-%d', Event.timestamp)
            format_str = '%Y-%m-%d'
        elif time_period == 'month':
            cutoff = cutoff - timedelta(days=30)
            group_by = func.strftime('%Y-%m-%d', Event.timestamp)
            format_str = '%Y-%m-%d'
        
        # Build the query
        query = db.session.query(
            group_by.label('period'),
            func.count(Event.id).label('count')
        ).filter(
            Event.project_id == project_id,
            Event.timestamp >= cutoff
        )
        
        # Add event_name filter if provided
        if event_name:
            query = query.filter(Event.event_name == event_name)
        
        # Group by time period and order by period
        query = query.group_by('period').order_by('period')
        
        # Execute query and process results
        results = query.all()
        
        # Format the result for Plotly
        periods = [r.period for r in results]
        counts = [r.count for r in results]
        
        return {
            'periods': periods,
            'counts': counts,
            'event_name': event_name,
            'time_period': time_period
        }
    
    @staticmethod
    def get_top_events(project_id, limit=10):
        """
        Get the most frequent events for a project
        """
        query = db.session.query(
            Event.event_name,
            func.count(Event.id).label('count')
        ).filter(
            Event.project_id == project_id
        ).group_by(
            Event.event_name
        ).order_by(
            desc('count')
        ).limit(limit)
        
        results = query.all()
        
        # Format the result for Plotly
        events = [r.event_name for r in results]
        counts = [r.count for r in results]
        
        return {
            'events': events,
            'counts': counts
        }
    
    @staticmethod
    def get_retention_data(project_id, weeks=8):
        """
        Calculate retention data for cohort analysis
        """
        # Get the cutoff date (8 weeks ago)
        cutoff = datetime.utcnow() - timedelta(weeks=weeks)
        
        # Get all users who had their first event in each week
        first_events = db.session.query(
            Event.user_id if Event.user_id is not None else Event.anonymous_id,
            func.min(Event.timestamp).label('first_seen')
        ).filter(
            Event.project_id == project_id,
            Event.timestamp >= cutoff
        ).group_by(
            Event.user_id if Event.user_id is not None else Event.anonymous_id
        ).subquery()
        
        # Group users into weekly cohorts
        user_cohorts = db.session.query(
            func.strftime('%Y-%W', first_events.c.first_seen).label('cohort'),
            func.count().label('count')
        ).group_by(
            'cohort'
        ).order_by(
            'cohort'
        ).all()
        
        # For each cohort, calculate retention in subsequent weeks
        retention_data = []
        for cohort_row in user_cohorts:
            cohort = cohort_row.cohort
            cohort_size = cohort_row.count
            
            # Initialize cohort data
            cohort_data = {
                'cohort': cohort,
                'size': cohort_size,
                'retention': {}
            }
            
            # Get users in this cohort
            cohort_users = db.session.query(
                Event.user_id if Event.user_id is not None else Event.anonymous_id
            ).filter(
                Event.project_id == project_id,
                func.strftime('%Y-%W', Event.timestamp) == cohort
            ).distinct().subquery()
            
            # For each subsequent week, calculate retention
            for week in range(weeks):
                target_date = datetime.strptime(f"{cohort}-1", "%Y-%W-%w") + timedelta(weeks=week)
                target_week = target_date.strftime('%Y-%W')
                
                # Count users from cohort who were active in target week
                retained_users = db.session.query(
                    func.count(func.distinct(Event.user_id if Event.user_id is not None else Event.anonymous_id))
                ).filter(
                    Event.project_id == project_id,
                    func.strftime('%Y-%W', Event.timestamp) == target_week,
                    (Event.user_id if Event.user_id is not None else Event.anonymous_id).in_(cohort_users)
                ).scalar() or 0
                
                # Calculate retention percentage
                retention_pct = round((retained_users / cohort_size) * 100, 1) if cohort_size > 0 else 0
                cohort_data['retention'][week] = retention_pct
            
            retention_data.append(cohort_data)
        
        return retention_data

class MLInsightService:
    @staticmethod
    def detect_anomalies(project_id, event_name=None, time_period='day'):
        """
        Detect anomalies in event frequency
        """
        # Get event frequency data
        frequency_data = AnalyticsService.get_event_frequency(project_id, event_name, time_period)
        
        # Convert to numpy array for analysis
        counts = np.array(frequency_data['counts'])
        
        # No data or insufficient data for anomaly detection
        if len(counts) < 3:
            return {
                'has_anomalies': False,
                'anomalies': [],
                'confidence': 0,
                'message': 'Insufficient data for anomaly detection'
            }
        
        # Simple anomaly detection using Z-score
        mean = np.mean(counts)
        std = np.std(counts)
        
        # If standard deviation is 0, no anomalies can be detected
        if std == 0:
            return {
                'has_anomalies': False,
                'anomalies': [],
                'confidence': 0,
                'message': 'No variance in data for anomaly detection'
            }
        
        # Calculate Z-scores
        z_scores = (counts - mean) / std
        
        # Define anomaly threshold (usually 3 sigma)
        threshold = 3
        
        # Find anomalies
        anomalies = []
        has_anomalies = False
        
        for i, z_score in enumerate(z_scores):
            if abs(z_score) > threshold:
                has_anomalies = True
                anomalies.append({
                    'period': frequency_data['periods'][i],
                    'count': int(counts[i]),
                    'z_score': round(float(z_score), 2),
                    'severity': 'high' if abs(z_score) > 4 else 'medium'
                })
        
        # Calculate confidence level based on data quantity
        confidence = min(0.5 + 0.05 * len(counts), 0.95)
        
        return {
            'has_anomalies': has_anomalies,
            'anomalies': anomalies,
            'confidence': round(confidence, 2),
            'message': 'Anomalies detected' if has_anomalies else 'No anomalies detected'
        }
    
    @staticmethod
    def get_user_segments(project_id):
        """
        Identify user segments based on behavior
        """
        # Get all events for this project
        events = db.session.query(
            Event.user_id,
            Event.anonymous_id,
            Event.event_name,
            func.count(Event.id).label('count')
        ).filter(
            Event.project_id == project_id
        ).group_by(
            Event.user_id,
            Event.anonymous_id,
            Event.event_name
        ).all()
        
        # Process events into user behavior profiles
        user_profiles = defaultdict(lambda: defaultdict(int))
        
        for event in events:
            user_id = event.user_id or event.anonymous_id
            user_profiles[user_id][event.event_name] = event.count
        
        # Simple segmentation based on event patterns
        segments = {
            'power_users': [],
            'casual_users': [],
            'new_users': [],
            'inactive_users': []
        }
        
        # Define thresholds for segmentation
        power_threshold = 20  # Users with > 20 total events
        new_threshold = 3     # Users with <= 3 total events
        
        for user_id, profile in user_profiles.items():
            total_events = sum(profile.values())
            
            if total_events > power_threshold:
                segments['power_users'].append(user_id)
            elif total_events <= new_threshold:
                segments['new_users'].append(user_id)
            else:
                segments['casual_users'].append(user_id)
        
        # Calculate segment metrics
        metrics = {
            'total_users': len(user_profiles),
            'segment_counts': {
                'power_users': len(segments['power_users']),
                'casual_users': len(segments['casual_users']),
                'new_users': len(segments['new_users']),
                'inactive_users': len(segments['inactive_users'])
            },
            'segment_percentages': {}
        }
        
        # Calculate percentages
        total = metrics['total_users']
        if total > 0:
            for segment, count in metrics['segment_counts'].items():
                metrics['segment_percentages'][segment] = round((count / total) * 100, 1)
        
        return {
            'segments': segments,
            'metrics': metrics
        }
    
    @staticmethod
    def analyze_sentiment(project_id, feedback_text):
        """
        Simple sentiment analysis of user feedback (placeholder)
        This would ideally use a proper NLP model
        """
        # Placeholder implementation - would be replaced with actual NLP
        positive_words = ['good', 'great', 'excellent', 'awesome', 'love', 'like', 'best', 'happy']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'dislike', 'worst', 'poor', 'disappointed']
        
        # Normalize text
        text = feedback_text.lower()
        
        # Count positive and negative words
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        # Calculate sentiment score (-1 to 1)
        total = positive_count + negative_count
        if total == 0:
            score = 0  # Neutral
        else:
            score = (positive_count - negative_count) / total
        
        # Determine sentiment category
        if score > 0.3:
            sentiment = 'positive'
        elif score < -0.3:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': round(score, 2),
            'confidence': 0.6  # Fixed confidence as this is a simple implementation
        }