import os
import json
import requests
from datetime import datetime, timedelta
import pandas as pd
from flask import current_app
from app.models import db
from app.models.event import Event
from app.models.project import Project

class DeepSeekMLInsights:
    """Service for providing advanced ML-powered insights and recommendations using DeepSeek API"""
    
    API_URL = "https://api.deepseek.com/v1/chat/completions"  # Replace with actual DeepSeek API endpoint
    
    @staticmethod
    def get_api_key():
        """Get DeepSeek API key from environment variable"""
        api_key = os.environ.get('DEEPSEEK_API_KEY')
        if not api_key:
            current_app.logger.warning("DeepSeek API key not found in environment variables")
            return None
        return api_key
    
    @classmethod
    def analyze_user_behavior(cls, project_id, time_period='week'):
        """
        Analyze user behavior patterns and provide insights and recommendations
        """
        # Get API key
        api_key = cls.get_api_key()
        if not api_key:
            return {
                'error': 'API key not configured',
                'message': 'DeepSeek API key not found. Please set the DEEPSEEK_API_KEY environment variable.'
            }
        
        # Get data for analysis
        data = cls._prepare_behavior_data(project_id, time_period)
        
        # Prepare prompt for DeepSeek
        prompt = cls._create_behavior_analysis_prompt(data)
        
        # Make API request
        try:
            response = cls._make_api_request(prompt, api_key)
            insights = cls._process_behavior_response(response)
            return insights
        except Exception as e:
            current_app.logger.error(f"Error analyzing user behavior with DeepSeek API: {str(e)}")
            return {
                'error': 'API request failed',
                'message': f"Failed to generate insights: {str(e)}"
            }
    
    @classmethod
    def get_product_recommendations(cls, project_id):
        """
        Get product improvement recommendations based on user behavior and feedback
        """
        # Get API key
        api_key = cls.get_api_key()
        if not api_key:
            return {
                'error': 'API key not configured',
                'message': 'DeepSeek API key not found. Please set the DEEPSEEK_API_KEY environment variable.'
            }
        
        # Get data for recommendations
        data = cls._prepare_recommendation_data(project_id)
        
        # Prepare prompt for DeepSeek
        prompt = cls._create_recommendation_prompt(data)
        
        # Make API request
        try:
            response = cls._make_api_request(prompt, api_key)
            recommendations = cls._process_recommendation_response(response)
            return recommendations
        except Exception as e:
            current_app.logger.error(f"Error generating recommendations with DeepSeek API: {str(e)}")
            return {
                'error': 'API request failed',
                'message': f"Failed to generate recommendations: {str(e)}"
            }
    
    @classmethod
    def _prepare_behavior_data(cls, project_id, time_period):
        """Prepare user behavior data for analysis"""
        # Determine cutoff date
        cutoff = datetime.utcnow()
        if time_period == 'day':
            cutoff = cutoff - timedelta(days=1)
        elif time_period == 'week':
            cutoff = cutoff - timedelta(days=7)
        elif time_period == 'month':
            cutoff = cutoff - timedelta(days=30)
        
        # Query events for the project
        events = db.session.query(
            Event.user_id,
            Event.anonymous_id,
            Event.event_name,
            Event.properties,
            Event.timestamp
        ).filter(
            Event.project_id == project_id,
            Event.timestamp >= cutoff
        ).order_by(
            Event.timestamp
        ).all()
        
        # Process events into a more usable format
        processed_events = []
        for event in events:
            user_id = event.user_id or event.anonymous_id
            processed_events.append({
                'user_id': user_id,
                'event_name': event.event_name,
                'properties': event.properties,
                'timestamp': event.timestamp.isoformat()
            })
        
        # Get unique users and their event sequences
        users = {}
        for event in processed_events:
            user_id = event['user_id']
            if user_id not in users:
                users[user_id] = []
            users[user_id].append({
                'event_name': event['event_name'],
                'timestamp': event['timestamp'],
                'properties': event['properties']
            })
        
        return {
            'time_period': time_period,
            'total_events': len(processed_events),
            'unique_users': len(users),
            'events': processed_events[:100],  # Limit to 100 events to avoid huge payloads
            'user_samples': dict(list(users.items())[:10])  # Sample of 10 users
        }
    
    @classmethod
    def _prepare_recommendation_data(cls, project_id):
        """Prepare data for product recommendations"""
        # Get project info
        project = Project.query.get(project_id)
        
        # Get event types and frequencies
        event_counts = db.session.query(
            Event.event_name,
            db.func.count(Event.id).label('count')
        ).filter(
            Event.project_id == project_id
        ).group_by(
            Event.event_name
        ).order_by(
            db.desc('count')
        ).all()
        
        event_frequencies = {event.event_name: event.count for event in event_counts}
        
        # Get user paths/flows - the sequence of events for each user
        user_paths_query = db.session.query(
            Event.user_id,
            Event.anonymous_id,
            Event.event_name,
            Event.timestamp
        ).filter(
            Event.project_id == project_id
        ).order_by(
            Event.user_id, 
            Event.anonymous_id,
            Event.timestamp
        ).all()
        
        # Process into user paths
        user_paths = {}
        for event in user_paths_query:
            user_id = event.user_id or event.anonymous_id
            if user_id not in user_paths:
                user_paths[user_id] = []
            user_paths[user_id].append({
                'event': event.event_name,
                'timestamp': event.timestamp.isoformat()
            })
        
        # Keep only a sample of user paths to limit payload size
        sample_paths = dict(list(user_paths.items())[:20])  # 20 user paths
        
        return {
            'project_name': project.name,
            'event_frequencies': event_frequencies,
            'sample_user_paths': sample_paths,
            'total_users': len(user_paths)
        }
    
    @classmethod
    def _create_behavior_analysis_prompt(cls, data):
        """Create prompt for user behavior analysis"""
        return [
            {"role": "system", "content": """You are an advanced analytics AI that provides insights on user behavior. 
            Analyze the provided event data and extract meaningful patterns, insights, and recommendations.
            Format your response in JSON with the following structure:
            {
                "insights": [
                    {"title": "Insight title", "description": "Detailed description of insight", "confidence": 0.8}
                ],
                "patterns": [
                    {"name": "Pattern name", "description": "Description of the pattern", "significance": "Why this matters"}
                ],
                "user_segments": [
                    {"name": "Segment name", "characteristics": "Description of this user group", "percentage": 30}
                ],
                "recommendations": [
                    {"title": "Recommendation", "description": "Details about what to do", "priority": "high/medium/low"}
                ]
            }
            Base your analysis on real patterns in the data. If there's not enough data, indicate this in your response.
            """},
            {"role": "user", "content": f"""Please analyze this user behavior data from a product analytics platform:
            
            Time period: {data['time_period']}
            Total events: {data['total_events']}
            Unique users: {data['unique_users']}
            
            Event samples:
            {json.dumps(data['events'][:10], indent=2)}
            
            User journey samples:
            {json.dumps(data['user_samples'], indent=2)}
            
            Provide insights on user behavior, identify patterns, suggest user segments, and make recommendations
            for improving the product based on this data.
            """}
        ]
    
    @classmethod
    def _create_recommendation_prompt(cls, data):
        """Create prompt for product recommendations"""
        return [
            {"role": "system", "content": """You are a product analytics expert that provides recommendations for product improvements.
            Analyze the provided data and generate actionable recommendations.
            Format your response in JSON with the following structure:
            {
                "key_findings": [
                    {"title": "Finding title", "description": "Detailed description", "impact": "high/medium/low"}
                ],
                "improvement_recommendations": [
                    {"title": "Recommendation", "description": "Details about what to implement", 
                     "expected_impact": "Description of potential positive outcomes", "effort": "high/medium/low", "priority": "high/medium/low"}
                ],
                "feature_ideas": [
                    {"name": "Feature name", "description": "What the feature would do", "rationale": "Why this would be valuable"}
                ],
                "engagement_strategies": [
                    {"name": "Strategy name", "description": "How to implement this strategy", "target_segment": "Which users this targets"}
                ]
            }
            Focus on actionable, specific recommendations based on the data patterns.
            """},
            {"role": "user", "content": f"""Please analyze this product data and provide recommendations for improvement:
            
            Project name: {data['project_name']}
            Total users: {data['total_users']}
            
            Event frequencies:
            {json.dumps(data['event_frequencies'], indent=2)}
            
            Sample user paths:
            {json.dumps(list(data['sample_user_paths'].values())[:5], indent=2)}
            
            Based on this data, provide recommendations for improving the product, increasing user engagement,
            and enhancing the overall user experience.
            """}
        ]
    
    @classmethod
    def _make_api_request(cls, prompt, api_key):
        """Make a request to the DeepSeek API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "deepseek-coder",  # Update with appropriate model name
            "messages": prompt,
            "temperature": 0.3,  # Lower temperature for more focused, analytical responses
            "max_tokens": 1500,
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(cls.API_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
        
        return response.json()
    
    @classmethod
    def _process_behavior_response(cls, response):
        """Process the API response for behavior analysis"""
        try:
            content = response['choices'][0]['message']['content']
            # Parse JSON response - the API should return JSON directly
            insights_data = json.loads(content)
            return insights_data
        except (KeyError, json.JSONDecodeError) as e:
            # If we can't parse JSON, try to extract from text
            raw_content = response['choices'][0]['message']['content']
            current_app.logger.error(f"Error parsing DeepSeek API response: {str(e)}")
            return {
                'error': 'Failed to parse API response',
                'raw_response': raw_content[:500]  # Include first 500 chars of raw response for debugging
            }
    
    @classmethod
    def _process_recommendation_response(cls, response):
        """Process the API response for recommendations"""
        try:
            content = response['choices'][0]['message']['content']
            # Parse JSON response
            recommendations_data = json.loads(content)
            return recommendations_data
        except (KeyError, json.JSONDecodeError) as e:
            # If we can't parse JSON, try to extract from text
            raw_content = response['choices'][0]['message']['content']
            current_app.logger.error(f"Error parsing DeepSeek API response: {str(e)}")
            return {
                'error': 'Failed to parse API response',
                'raw_response': raw_content[:500]  # Include first 500 chars of raw response for debugging
            }
    
    @classmethod
    def generate_mock_insights(cls):
        """Generate mock insights when API is not available"""
        return {
            "insights": [
                {"title": "Peak Usage Time", "description": "Users are most active between 10am-2pm on weekdays", "confidence": 0.9},
                {"title": "Feature Adoption", "description": "Only 25% of users are utilizing the advanced search functionality", "confidence": 0.85},
                {"title": "Drop-off Point", "description": "20% of users abandon the checkout process at the payment method selection", "confidence": 0.78}
            ],
            "patterns": [
                {"name": "Browse-Add-Abandon", "description": "Users browse products, add to cart, but don't complete purchase", "significance": "Cart abandonment indicates potential UX issues at checkout"},
                {"name": "Search-Filter-Exit", "description": "Users search, apply filters, then exit without selection", "significance": "Search results may not match user expectations"}
            ],
            "user_segments": [
                {"name": "Power Users", "characteristics": "Uses product daily, engages with advanced features", "percentage": 15},
                {"name": "Casual Browsers", "characteristics": "Visits occasionally, rarely completes key actions", "percentage": 40},
                {"name": "Task-Focused Users", "characteristics": "Visits with specific goal, completes quickly and leaves", "percentage": 30}
            ],
            "recommendations": [
                {"title": "Simplify Checkout Process", "description": "Reduce steps in checkout flow from 5 to 3", "priority": "high"},
                {"title": "Improve Search Relevance", "description": "Implement semantic search to better match user intent", "priority": "medium"},
                {"title": "Feature Education", "description": "Add tooltips for advanced features to increase adoption", "priority": "medium"}
            ]
        }
    
    @classmethod
    def generate_mock_recommendations(cls):
        """Generate mock recommendations when API is not available"""
        return {
            "key_findings": [
                {"title": "High Bounce Rate on Landing Page", "description": "42% of users leave without interacting with any elements", "impact": "high"},
                {"title": "Underutilized Features", "description": "Premium features have less than 5% usage rate", "impact": "medium"},
                {"title": "Mobile Conversion Gap", "description": "Mobile users convert at 40% lower rate than desktop", "impact": "high"}
            ],
            "improvement_recommendations": [
                {"title": "Redesign Landing Page", "description": "Simplify messaging and add clear CTAs above the fold", 
                 "expected_impact": "15-20% reduction in bounce rate", "effort": "medium", "priority": "high"},
                {"title": "Feature Highlight Campaign", "description": "Create in-app tours for premium features", 
                 "expected_impact": "30% increase in feature adoption", "effort": "low", "priority": "medium"},
                {"title": "Optimize Mobile Checkout", "description": "Streamline mobile form fields and payment process", 
                 "expected_impact": "25% increase in mobile conversion", "effort": "high", "priority": "high"}
            ],
            "feature_ideas": [
                {"name": "One-Click Reorder", "description": "Allow users to quickly repeat previous purchases", 
                 "rationale": "Increases repeat purchase rate and customer lifetime value"},
                {"name": "Personalized Recommendations", "description": "Show tailored suggestions based on browsing history", 
                 "rationale": "Increases average order value and engagement time"}
            ],
            "engagement_strategies": [
                {"name": "Re-engagement Email Series", "description": "3-email sequence for inactive users with personalized offers", 
                 "target_segment": "Users inactive for 30+ days"},
                {"name": "Progress Milestones", "description": "Celebrate user achievements with in-app notifications", 
                 "target_segment": "Regular users who haven't upgraded"}
            ]
        }