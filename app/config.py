import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Get the absolute base directory of the application
basedir = Path(__file__).parent.parent.absolute()

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Use absolute path with normalized slashes for macOS
    instance_path = os.path.normpath(os.path.join(basedir, 'instance'))
    if not os.path.exists(instance_path):
        os.makedirs(instance_path, exist_ok=True)
        print(f"Created instance directory: {instance_path}")
    
    # Create an absolute path to the database
    instance_db_path = os.path.normpath(os.path.join(instance_path, 'analytics.db'))
    
    # Always use 4 slashes for absolute paths in SQLite URI
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{instance_db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Print the database path for debugging
    print(f"Instance directory: {instance_path}")
    print(f"Database URI: {SQLALCHEMY_DATABASE_URI}")
    
    # DeepSeek API settings
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
