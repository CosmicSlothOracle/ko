import os
from typing import List

# Base Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
PARTICIPANTS_FILE = os.path.join(BASE_DIR, 'participants.json')

# File Upload Settings
MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# CORS Settings
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else [
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
    "https://kos-frontend-kqxo-kqxo.onrender.com",
    "https://kosge.netlify.app",
    "https://kosge.onrender.com"
]

# Authentication Settings
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', 
    b'$2b$12$ZCgWXzUdmVX.PnIfj4oeJOkX69Tu1rVZ51zGYe3kSloANnwMaTlBW')

ADMIN_USER = {
    'username': ADMIN_USERNAME,
    'password_hash': ADMIN_PASSWORD_HASH
}

# Content Management Settings
SUPPORTED_LANGUAGES = ['de', 'en', 'tr', 'ru', 'ar']
DEFAULT_LANGUAGE = 'de'

# Security Settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
DEBUG = os.environ.get('FLASK_ENV') == 'development'

# Logging Settings
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def init_directories():
    """Initialize required directories"""
    try:
        directories = [
            UPLOAD_FOLDER,
            os.path.join(BASE_DIR, 'content')
        ]

        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)

        # Create language directories
        content_dir = os.path.join(BASE_DIR, 'content')
        for lang in SUPPORTED_LANGUAGES:
            lang_dir = os.path.join(content_dir, lang)
            if not os.path.exists(lang_dir):
                os.makedirs(lang_dir)
    except Exception as e:
        print(f"Error creating directories: {e}")
        raise

def init_participants_file():
    """Initialize participants file if it doesn't exist"""
    try:
        if not os.path.exists(PARTICIPANTS_FILE):
            with open(PARTICIPANTS_FILE, 'w', encoding='utf-8') as f:
                f.write('[]')
    except Exception as e:
        print(f"Error creating participants file: {e}")
        raise

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check if upload folder is writable
    if not os.access(os.path.dirname(UPLOAD_FOLDER), os.W_OK):
        errors.append(f"Upload directory is not writable: {UPLOAD_FOLDER}")
    
    # Check if participants file directory is writable
    if not os.access(os.path.dirname(PARTICIPANTS_FILE), os.W_OK):
        errors.append(f"Participants file directory is not writable: {os.path.dirname(PARTICIPANTS_FILE)}")
    
    # Validate CORS origins
    if not CORS_ORIGINS:
        errors.append("No CORS origins configured")
    
    # Check for default secret key in production
    if not DEBUG and SECRET_KEY == 'your-secret-key-change-in-production':
        errors.append("Default secret key detected in production environment")
    
    return errors

def init():
    """Initialize all required configurations"""
    try:
        init_directories()
        init_participants_file()
        
        # Validate configuration
        config_errors = validate_config()
        if config_errors:
            print("Configuration validation errors:")
            for error in config_errors:
                print(f"  - {error}")
            if not DEBUG:
                raise ValueError("Configuration validation failed")
    except Exception as e:
        print(f"Initialization failed: {e}")
        raise

# Initialize on import
init()
