from flask import Flask, jsonify, request, send_from_directory, make_response, redirect, session
from flask_cors import CORS
import bcrypt
import os
import json
import re
import secrets
from datetime import datetime
from werkzeug.utils import secure_filename
from cms import ContentManager
import logging
from config import (
    UPLOAD_FOLDER, PARTICIPANTS_FILE, ADMIN_USER,
    CORS_ORIGINS, MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS, BASE_DIR, init
)

# Configure logging based on environment
log_level = logging.DEBUG if os.environ.get('FLASK_ENV') == 'development' else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": CORS_ORIGINS,
        "methods": ["GET", "POST", "DELETE", "OPTIONS", "PUT"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Initialize CMS
content_manager = ContentManager(
    os.path.join(BASE_DIR, 'content'))

logger.info(f'Base directory: {BASE_DIR}')
logger.info(f'Upload folder: {UPLOAD_FOLDER}')

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    logger.info(f'Creating upload directory: {UPLOAD_FOLDER}')
    os.makedirs(UPLOAD_FOLDER)
    logger.info('Upload directory created successfully')

# Create empty participants file if it doesn't exist
if not os.path.exists(PARTICIPANTS_FILE):
    with open(PARTICIPANTS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

# Add debug logging for participants file
logger.info(f'Participants file path: {PARTICIPANTS_FILE}')
if os.path.exists(PARTICIPANTS_FILE):
    logger.info('Participants file exists')
    with open(PARTICIPANTS_FILE, 'r', encoding='utf-8') as f:
        try:
            participants = json.load(f)
            logger.info(f'Number of participants: {len(participants)}')
        except json.JSONDecodeError as e:
            logger.error(f'Error reading participants file: {e}')
else:
    logger.warning('Participants file does not exist')

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# CSRF Protection
def generate_csrf_token():
    """Generate CSRF token for forms"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def validate_csrf_token(token):
    """Validate CSRF token"""
    return token == session.get('csrf_token')

def require_csrf_token(f):
    """Decorator to require CSRF token for POST requests"""
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            # Get token from header or form data
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            
            if not token:
                logger.warning('CSRF token missing in request')
                return jsonify({'error': 'CSRF token required'}), 403
            
            if not validate_csrf_token(token):
                logger.warning('Invalid CSRF token in request')
                return jsonify({'error': 'Invalid CSRF token'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# CSRF token endpoint
@app.route('/api/csrf-token', methods=['GET'])
def get_csrf_token():
    """Get CSRF token for forms"""
    token = generate_csrf_token()
    return jsonify({'csrf_token': token}), 200

# Event limits configuration
EVENT_LIMITS = {
    'max_participants_per_event': int(os.environ.get('MAX_PARTICIPANTS_PER_EVENT', 100)),
    'max_events_per_user': int(os.environ.get('MAX_EVENTS_PER_USER', 5)),
    'max_file_size_mb': int(os.environ.get('MAX_FILE_SIZE_MB', 16))
}

def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = request.headers.get(
        'Origin')
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS, PUT'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


@app.after_request
def after_request(response):
    return add_cors_headers(response)


@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin",
                             request.headers.get('Origin'))
        response.headers.add("Access-Control-Allow-Methods",
                             "GET, POST, DELETE, OPTIONS, PUT")
        response.headers.add("Access-Control-Allow-Headers",
                             "Content-Type, Authorization")
        return response


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def load_participants():
    if not os.path.exists(PARTICIPANTS_FILE):
        return []
    try:
        with open(PARTICIPANTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f'JSON decode error in participants file: {e}')
        return []
    except Exception as e:
        logger.error(f'Unexpected error loading participants: {e}')
        return []


def save_participants(participants):
    try:
        with open(PARTICIPANTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(participants, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f'Error saving participants: {e}')
        raise


def validate_email(email):
    """Validate email format"""
    if not email:
        return True  # Email is optional
    return bool(EMAIL_REGEX.match(email))


def validate_participant_data(data):
    """Validate participant data with comprehensive rules"""
    errors = []
    
    # Name validation
    name = data.get('name', '').strip()
    if not name:
        errors.append('Name is required')
    elif len(name) < 2:
        errors.append('Name must be at least 2 characters long')
    elif len(name) > 100:
        errors.append('Name must be less than 100 characters long')
    elif not name.replace(' ', '').isalpha():
        errors.append('Name should only contain letters and spaces')
    
    # Email validation
    email = data.get('email', '').strip()
    if email:  # Email is optional
        if not validate_email(email):
            errors.append('Invalid email format')
        elif len(email) > 254:
            errors.append('Email address is too long')
    
    # Message validation
    message = data.get('message', '').strip()
    if message and len(message) > 1000:
        errors.append('Message must be less than 1000 characters')
    
    # Banner validation
    banner = data.get('banner')
    if banner:
        if not isinstance(banner, str):
            errors.append('Banner must be a string')
        elif len(banner) > 500:
            errors.append('Banner URL is too long')
        elif not banner.startswith(('http://', 'https://', '/')):
            errors.append('Invalid banner URL format')
    
    # Event validation
    event = data.get('event')
    if event:
        if not isinstance(event, str):
            errors.append('Event must be a string')
        elif len(event) > 100:
            errors.append('Event name is too long')
    
    return errors


def validate_participant_update(data, participant_id):
    """Validate participant update data"""
    errors = []
    
    # Check if participant exists
    participants = load_participants()
    if participant_id >= len(participants):
        errors.append('Participant not found')
        return errors
    
    # Validate update data
    errors.extend(validate_participant_data(data))
    
    return errors


def sanitize_participant_data(data):
    """Sanitize participant data to prevent XSS and other attacks"""
    import html
    
    sanitized = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            # HTML escape to prevent XSS
            sanitized[key] = html.escape(value.strip())
        else:
            sanitized[key] = value
    
    return sanitized


def check_participant_limits():
    """Check if participant limits are reached"""
    participants = load_participants()
    max_participants = EVENT_LIMITS['max_participants_per_event']
    
    if len(participants) >= max_participants:
        return False, f'Event is full. Maximum {max_participants} participants allowed.'
    
    return True, None


def validate_file_upload(file):
    """Validate file upload"""
    errors = []
    
    if not file:
        errors.append('No file provided')
        return errors
    
    # Check file size
    max_size = EVENT_LIMITS['max_file_size_mb'] * 1024 * 1024  # Convert to bytes
    if file.content_length and file.content_length > max_size:
        errors.append(f'File size exceeds maximum limit of {EVENT_LIMITS["max_file_size_mb"]}MB')
    
    # Check file type
    if not allowed_file(file.filename):
        errors.append(f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}')
    
    # Check filename
    if file.filename:
        if len(file.filename) > 255:
            errors.append('Filename is too long')
        elif not file.filename.replace('.', '').replace('-', '').replace('_', '').isalnum():
            errors.append('Filename contains invalid characters')
    
    return errors


def validate_password(password):
    """Validate password strength with comprehensive rules"""
    errors = []
    
    if not password:
        errors.append('Password is required')
        return errors
    
    # Length validation
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    elif len(password) > 128:
        errors.append('Password must be less than 128 characters long')
    
    # Character type validation
    if not any(c.isupper() for c in password):
        errors.append('Password must contain at least one uppercase letter')
    
    if not any(c.islower() for c in password):
        errors.append('Password must contain at least one lowercase letter')
    
    if not any(c.isdigit() for c in password):
        errors.append('Password must contain at least one number')
    
    # Special character validation (optional but recommended)
    special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
    if not any(c in special_chars for c in password):
        errors.append('Password should contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)')
    
    # Common password check
    common_passwords = [
        'password', '123456', '12345678', 'qwerty', 'abc123',
        'password123', 'admin', 'letmein', 'welcome', 'monkey'
    ]
    if password.lower() in common_passwords:
        errors.append('Password is too common, please choose a more secure password')
    
    # Sequential characters check
    if len(password) >= 3:
        for i in range(len(password) - 2):
            if (password[i].isdigit() and password[i+1].isdigit() and password[i+2].isdigit() and
                int(password[i+1]) == int(password[i]) + 1 and int(password[i+2]) == int(password[i+1]) + 1):
                errors.append('Password should not contain sequential numbers')
                break
    
    return errors


def validate_password_change(old_password, new_password, confirm_password):
    """Validate password change with additional checks"""
    errors = []
    
    # Basic new password validation
    errors.extend(validate_password(new_password))
    
    # Confirm password check
    if new_password != confirm_password:
        errors.append('New password and confirmation password do not match')
    
    # Old password check (if provided)
    if old_password and old_password == new_password:
        errors.append('New password must be different from the old password')
    
    return errors


@app.route('/api/health', methods=['GET'])
def health():
    try:
        # Check if we can read participants file
        participants = load_participants()
        # Check if uploads directory exists
        uploads_exist = os.path.exists(UPLOAD_FOLDER)

        return jsonify({
            'status': 'healthy',
            'participants_count': len(participants),
            'uploads_directory': uploads_exist,
            'base_dir': BASE_DIR,
            'python_version': os.environ.get('PYTHON_VERSION', '3.11.11'),
            'environment': os.environ.get('FLASK_ENV', 'production'),
            'event_limits': EVENT_LIMITS
        }), 200
    except Exception as e:
        logger.error(f'Health check failed: {str(e)}')
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Validate password strength
        password_errors = validate_password(password)
        if password_errors:
            return jsonify({'error': 'Password validation failed', 'details': password_errors}), 400
            
        if username == ADMIN_USER['username'] and bcrypt.checkpw(password.encode(), ADMIN_USER['password_hash']):
            # Dummy-Token (später JWT)
            return jsonify({'token': 'dummy-token', 'user': username}), 200
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        logger.error(f'Login error: {e}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/banners', methods=['POST'])
@require_csrf_token
def upload_banner():
    if 'file' not in request.files:
        logger.error('No file part in request')
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        logger.error('No selected file')
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        logger.info(f'Saving file to: {save_path}')
        try:
            file.save(save_path)
            logger.info(f'File saved successfully: {save_path}')
            # Verify file exists after saving
            if os.path.exists(save_path):
                logger.info(f'File exists at: {save_path}')
                logger.info(f'File size: {os.path.getsize(save_path)} bytes')
            else:
                logger.error(f'File not found after saving: {save_path}')
            url = f'/api/uploads/{filename}'
            return jsonify({'url': url, 'filename': filename}), 201
        except Exception as e:
            logger.error(f'Error saving file: {str(e)}')
            return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
    logger.error('Invalid file type')
    return jsonify({'error': f'Invalid file type. Only {", ".join(ALLOWED_EXTENSIONS)} allowed.'}), 400


@app.route('/api/banners', methods=['GET'])
def list_banners():
    try:
        files = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)]
        urls = [f'/api/uploads/{f}' for f in files]
        return jsonify({'banners': urls}), 200
    except Exception as e:
        logger.error(f'Error listing banners: {e}')
        return jsonify({'error': 'Failed to list banners'}), 500


@app.route('/api/banners/<filename>', methods=['DELETE'])
def delete_banner(filename):
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not allowed_file(filename):
            return jsonify({'error': 'Invalid file type.'}), 400
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True, 'filename': filename}), 200
        else:
            return jsonify({'error': 'File not found.'}), 404
    except Exception as e:
        logger.error(f'Error deleting banner: {e}')
        return jsonify({'error': 'Failed to delete banner'}), 500


@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    logger.info(f'Attempting to serve file: {filename}')
    logger.info(f'Upload folder: {UPLOAD_FOLDER}')
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    logger.info(f'Full file path: {file_path}')

    if not os.path.exists(file_path):
        logger.error(f'File not found: {file_path}')
        return jsonify({'error': 'File not found'}), 404

    try:
        logger.info(f'File exists, size: {os.path.getsize(file_path)} bytes')
        response = send_from_directory(UPLOAD_FOLDER, filename)

        # Use the add_cors_headers function
        response = add_cors_headers(response)

        # Set content type for image files
        if filename.lower().endswith('.png'):
            response.headers['Content-Type'] = 'image/png'
        elif filename.lower().endswith(('.jpg', '.jpeg')):
            response.headers['Content-Type'] = 'image/jpeg'
        elif filename.lower().endswith('.gif'):
            response.headers['Content-Type'] = 'image/gif'

        return response
    except Exception as e:
        logger.error(f'Error serving file {filename}: {str(e)}')
        return jsonify({'error': f'Error serving file: {str(e)}'}), 500


@app.route('/api/participants', methods=['POST'])
@require_csrf_token
def add_participant():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Sanitize input data
        sanitized_data = sanitize_participant_data(data)
        
        # Validate input data
        validation_errors = validate_participant_data(sanitized_data)
        if validation_errors:
            return jsonify({'error': 'Validation failed', 'details': validation_errors}), 400
        
        # Check event limits
        can_add, limit_message = check_participant_limits()
        if not can_add:
            return jsonify({'error': limit_message}), 400
        
        name = sanitized_data.get('name', '').strip()
        email = sanitized_data.get('email', '').strip()
        message = sanitized_data.get('message', '').strip()
        banner = sanitized_data.get('banner')
        event = sanitized_data.get('event')
        
        participant = {
            'name': name,
            'email': email,
            'message': message,
            'banner': banner,
            'event': event,
            'timestamp': datetime.now().isoformat(),
            'id': generate_participant_id()
        }
        
        participants = load_participants()
        participants.append(participant)
        save_participants(participants)
        
        logger.info(f'New participant added: {name} ({email})')
        return jsonify({'success': True, 'participant': participant}), 201
    except Exception as e:
        logger.error(f'Error adding participant: {e}')
        return jsonify({'error': 'Failed to add participant'}), 500


def generate_participant_id():
    """Generate unique participant ID"""
    import uuid
    return str(uuid.uuid4())[:8]


@app.route('/api/participants/<int:participant_id>', methods=['PUT'])
def update_participant(participant_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate update data
        validation_errors = validate_participant_update(data, participant_id)
        if validation_errors:
            return jsonify({'error': 'Validation failed', 'details': validation_errors}), 400
        
        # Sanitize input data
        sanitized_data = sanitize_participant_data(data)
        
        participants = load_participants()
        if participant_id >= len(participants):
            return jsonify({'error': 'Participant not found'}), 404
        
        # Update participant
        participants[participant_id].update(sanitized_data)
        participants[participant_id]['updated_at'] = datetime.now().isoformat()
        
        save_participants(participants)
        
        logger.info(f'Participant updated: ID {participant_id}')
        return jsonify({'success': True, 'participant': participants[participant_id]}), 200
    except Exception as e:
        logger.error(f'Error updating participant: {e}')
        return jsonify({'error': 'Failed to update participant'}), 500


@app.route('/api/participants/<int:participant_id>', methods=['DELETE'])
def delete_participant(participant_id):
    try:
        participants = load_participants()
        if participant_id >= len(participants):
            return jsonify({'error': 'Participant not found'}), 404
        
        deleted_participant = participants.pop(participant_id)
        save_participants(participants)
        
        logger.info(f'Participant deleted: ID {participant_id}')
        return jsonify({'success': True, 'deleted_participant': deleted_participant}), 200
    except Exception as e:
        logger.error(f'Error deleting participant: {e}')
        return jsonify({'error': 'Failed to delete participant'}), 500


@app.route('/api/participants/stats', methods=['GET'])
def get_participant_stats():
    try:
        participants = load_participants()
        
        stats = {
            'total_participants': len(participants),
            'max_participants': EVENT_LIMITS['max_participants_per_event'],
            'available_slots': EVENT_LIMITS['max_participants_per_event'] - len(participants),
            'events': {},
            'recent_participants': participants[-10:] if participants else []
        }
        
        # Count participants by event
        for participant in participants:
            event = participant.get('event', 'Unknown')
            stats['events'][event] = stats['events'].get(event, 0) + 1
        
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f'Error getting participant stats: {e}')
        return jsonify({'error': 'Failed to get participant stats'}), 500


@app.route('/api/participants', methods=['GET'])
def get_participants():
    try:
        participants = load_participants()
        response = jsonify({'participants': participants})
        # Use the after_request handler to add CORS headers
        return response, 200
    except Exception as e:
        logger.error(f'Error getting participants: {str(e)}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/participants', methods=['OPTIONS'])
def participants_options():
    return create_options_response()


# Reusable function for OPTIONS response
def create_options_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin",
                         request.headers.get('Origin'))
    response.headers.add("Access-Control-Allow-Methods",
                         "GET, POST, DELETE, OPTIONS, PUT")
    response.headers.add("Access-Control-Allow-Headers",
                         "Content-Type, Authorization")
    return response


# CMS Routes
@app.route('/api/cms/content/<section>', methods=['GET'])
def get_content(section):
    try:
        language = request.args.get('language')
        content = content_manager.get_content(section, language)
        if content:
            return jsonify(content), 200
        return jsonify({'error': 'Content not found'}), 404
    except Exception as e:
        logger.error(f'Error getting content: {e}')
        return jsonify({'error': 'Failed to get content'}), 500


@app.route('/api/cms/content/<section>', methods=['POST'])
@require_csrf_token
def create_content(section):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        title = data.get('title')
        content = data.get('content')
        metadata = data.get('metadata', {})

        if not all([title, content]):
            return jsonify({'error': 'Title and content are required'}), 400

        success = content_manager.create_content(section, title, content, metadata)
        if success:
            return jsonify({'success': True, 'section': section}), 201
        return jsonify({'error': 'Failed to create content'}), 500
    except Exception as e:
        logger.error(f'Error creating content: {e}')
        return jsonify({'error': 'Failed to create content'}), 500


@app.route('/api/cms/content/<section>', methods=['PUT'])
@require_csrf_token
def update_content(section):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        content = data.get('content')
        metadata = data.get('metadata', {})
        language = data.get('language')

        if not content:
            return jsonify({'error': 'Content is required'}), 400

        success = content_manager.update_content(
            section, content, metadata, language)
        if success:
            return jsonify({'success': True, 'section': section}), 200
        return jsonify({'error': 'Failed to update content'}), 404
    except Exception as e:
        logger.error(f'Error updating content: {e}')
        return jsonify({'error': 'Failed to update content'}), 500


@app.route('/api/cms/content/<section>/translate/<target_language>', methods=['POST'])
@require_csrf_token
def translate_content(section, target_language):
    try:
        success = content_manager.translate_content(section, target_language)
        if success:
            return jsonify({'success': True, 'section': section, 'language': target_language}), 200
        return jsonify({'error': 'Translation failed'}), 400
    except Exception as e:
        logger.error(f'Error translating content: {e}')
        return jsonify({'error': 'Translation failed'}), 500


@app.route('/api/cms/sections', methods=['GET'])
def list_sections():
    try:
        language = request.args.get('language')
        sections = content_manager.list_sections(language)
        return jsonify({'sections': sections}), 200
    except Exception as e:
        logger.error(f'Error listing sections: {e}')
        return jsonify({'error': 'Failed to list sections'}), 500


@app.route('/api/cms/content/<section>', methods=['DELETE'])
@require_csrf_token
def delete_content(section):
    try:
        language = request.args.get('language')
        success = content_manager.delete_content(section, language)
        if success:
            return jsonify({'success': True}), 200
        return jsonify({'error': 'Content not found'}), 404
    except Exception as e:
        logger.error(f'Error deleting content: {e}')
        return jsonify({'error': 'Failed to delete content'}), 500


# Add a root route that redirects to frontend or shows API status
@app.route('/')
def index():
    # Check if this is a browser request (has Accept header with text/html)
    if 'text/html' in request.headers.get('Accept', ''):
        # Redirect to frontend
        return redirect('https://kosge-frontend.onrender.com')
    # Otherwise return API status as JSON
    return jsonify({
        'status': 'online',
        'message': 'KOSGE API Server',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health',
            'login': '/api/login',
            'banners': '/api/banners',
            'participants': '/api/participants',
            'cms': '/api/cms/content/<section>'
        }
    }), 200


# Add a route for favicon.ico to prevent 404 errors
@app.route('/favicon.ico')
def favicon():
    return '', 204  # Return no content status


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
