#!/usr/bin/env python
"""
Direct SQLite database creation script

This script bypasses SQLAlchemy to create the database file first,
then initializes the schema and adds a test user.
"""
import os
import sys
import sqlite3
from pathlib import Path

def create_database():
    """Create database using direct SQLite approach"""
    try:
        # Get absolute path to the project directory
        basedir = Path(__file__).resolve().parent
        print(f"Absolute file path: {os.path.abspath(__file__)}")
        print(f"Base directory: {basedir}")
        
        # Create a database path in the project root
        db_path = basedir / 'product_analytics.db'
        print(f"Project root database path: {db_path}")
        
        # Ensure the instance directory exists
        instance_dir = basedir / 'instance'
        if not instance_dir.exists():
            os.makedirs(instance_dir)
            print(f"Created instance directory at {instance_dir}")
        
        # Create a database path in the instance folder (where Flask expects it)
        instance_db_path = instance_dir / 'analytics.db'
        print(f"Instance database path: {instance_db_path}")
        
        # Remove existing files if they exist
        if db_path.exists():
            os.remove(db_path)
            print(f"Removed existing database at {db_path}")
        
        if instance_db_path.exists():
            os.remove(instance_db_path)
            print(f"Removed existing database at {instance_db_path}")
        
        # Create empty SQLite databases
        conn = sqlite3.connect(str(db_path))
        conn.close()
        os.chmod(db_path, 0o666)
        print(f"Created empty database file at: {db_path}")
        
        conn = sqlite3.connect(str(instance_db_path))
        conn.close()
        os.chmod(instance_db_path, 0o666)
        print(f"Created empty database file at: {instance_db_path}")
        
        # Set environment variable for the database path to use the instance path
        os.environ['DATABASE_URL'] = f'sqlite:///{instance_db_path}'
        print(f"Set DATABASE_URL environment variable to: {os.environ['DATABASE_URL']}")
        
        # Now create the tables using SQLAlchemy
        from app import create_app, db
        from app.models.user import User
        
        # Create and configure the application
        app = create_app()
        
        # Create tables and test user
        with app.app_context():
            # Create all tables
            db.create_all()
            print("Created database tables.")
            
            # Create a test admin user
            from werkzeug.security import generate_password_hash
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=generate_password_hash("admin123")
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Created admin user (username: admin, password: admin123)")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Creating database...")
    if create_database():
        print("Database created successfully.")
        sys.exit(0)
    else:
        print("Database creation failed.")
        sys.exit(1)