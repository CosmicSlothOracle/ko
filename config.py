import os

# Base Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
PARTICIPANTS_FILE = os.path.join(BASE_DIR, 'participants.json')

# File Upload Settings
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# CORS Settings - Netlify Frontend + Render Backend


def get_cors_origins():
    """Get CORS origins from environment variable"""
    cors_env = os.getenv('CORS_ORIGINS')
    if cors_env:
        return [origin.strip() for origin in cors_env.split(',')]

    # Fallback for development
    return [
        "http://localhost:8000",  # Local development
        "http://127.0.0.1:8000",  # Local development
        "https://berlin-kosge.netlify.app",  # Production frontend (Netlify)
        "https://kosge-backend.onrender.com",  # Production backend (Render)
    ]


CORS_ORIGINS = get_cors_origins()

# Authentication Settings


def get_admin_user():
    """Get admin user from environment variables"""
    username = os.getenv('ADMIN_USERNAME', 'admin')
    password_hash = os.getenv('ADMIN_PASSWORD_HASH')

    if not password_hash:
        # Fallback for development - DO NOT USE IN PRODUCTION
        password_hash = '$2b$12$adwRmBSof8bRpwiTnhnr..a0fv4RVnF5GJOJ9H4hUCQpmYa.3SWc6'

    return {
        'username': username,
        'password_hash': password_hash.encode() if isinstance(password_hash, str) else password_hash
    }


ADMIN_USER = get_admin_user()

# Content Management Settings
SUPPORTED_LANGUAGES = ['de', 'en', 'tr', 'ru', 'ar']
DEFAULT_LANGUAGE = 'de'

# Create required directories


def init_directories():
    """Initialize required directories"""
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

# Create empty participants file if it doesn't exist


def init_participants_file():
    """Initialize participants file if it doesn't exist"""
    if not os.path.exists(PARTICIPANTS_FILE):
        with open(PARTICIPANTS_FILE, 'w', encoding='utf-8') as f:
            f.write('[]')


def init():
    """Initialize all required configurations"""
    init_directories()
    init_participants_file()


# Initialize on import
init()
