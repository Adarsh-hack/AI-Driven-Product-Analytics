#!/usr/bin/env python
"""
Database permission fix script for macOS

This script focuses on creating the database file with proper permissions
and ownership to resolve common macOS SQLite access issues.
"""
import os
import sys
import sqlite3
import stat
from pathlib import Path
import subprocess

def fix_database():
    """Fix database permissions and ownership"""
    try:
        # Get absolute path to the project directory
        basedir = Path(__file__).resolve().parent
        print(f"Base directory: {basedir}")
        
        # Ensure the instance directory exists with proper permissions
        instance_dir = basedir / 'instance'
        if not instance_dir.exists():
            os.makedirs(instance_dir, exist_ok=True)
            print(f"Created instance directory at {instance_dir}")
        
        # Set liberal permissions on the instance directory
        os.chmod(instance_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
        print(f"Set permissions on instance directory: {oct(os.stat(instance_dir).st_mode)}")
        
        # Define database path
        db_path = instance_dir / 'analytics.db'
        print(f"Database path: {db_path}")
        
        # Remove existing file if it exists
        if db_path.exists():
            os.remove(db_path)
            print(f"Removed existing database at {db_path}")
        
        # Create an empty SQLite database
        conn = sqlite3.connect(str(db_path))
        conn.close()
        
        # Set very permissive file permissions (read/write for everyone)
        os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)  # 0666
        print(f"Created database file with permissions: {oct(os.stat(db_path).st_mode)}")
        
        # Ensure current user is the owner of the file
        subprocess.run(['whoami'], capture_output=True, text=True)
        print(f"Current user: {subprocess.run(['whoami'], capture_output=True, text=True).stdout.strip()}")
        
        # Check file ownership
        file_info = subprocess.run(['ls', '-la', str(db_path)], capture_output=True, text=True)
        print(f"File ownership: {file_info.stdout.strip()}")
        
        # Now initialize the database schema
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
        
        # Verify the database file still has correct permissions after SQLAlchemy operations
        print(f"Final database permissions: {oct(os.stat(db_path).st_mode)}")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Fixing database permissions...")
    if fix_database():
        print("Database created successfully with proper permissions.")
        sys.exit(0)
    else:
        print("Database creation failed.")
        sys.exit(1)