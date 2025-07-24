from flask import Flask, jsonify, request, send_from_directory, make_response, redirect
from flask_cors import CORS
import bcrypt
import os
import json
import re
from werkzeug.utils import secure_filename
from cms import ContentManager
import logging
from config import (
    UPLOAD_FOLDER, PARTICIPANTS_FILE, ADMIN_USER,
    CORS_ORIGINS, MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS, init
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
    os.path.join(os.path.dirname(__file__), 'content'))

# Get the absolute path of the current directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

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
    """Validate participant data"""
    errors = []
    
    name = data.get('name', '').strip()
    if not name or len(name) < 2:
        errors.append('Name must be at least 2 characters long')
    
    email = data.get('email', '').strip()
    if email and not validate_email(email):
        errors.append('Invalid email format')
    
    message = data.get('message', '').strip()
    if message and len(message) > 1000:
        errors.append('Message must be less than 1000 characters')
    
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
            'environment': os.environ.get('FLASK_ENV', 'production')
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
            
        if username == ADMIN_USER['username'] and bcrypt.checkpw(password.encode(), ADMIN_USER['password_hash']):
            # Dummy-Token (später JWT)
            return jsonify({'token': 'dummy-token', 'user': username}), 200
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        logger.error(f'Login error: {e}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/banners', methods=['POST'])
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
def add_participant():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Validate input data
        validation_errors = validate_participant_data(data)
        if validation_errors:
            return jsonify({'error': 'Validation failed', 'details': validation_errors}), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        banner = data.get('banner')
        
        participant = {
            'name': name,
            'email': email,
            'message': message,
            'banner': banner
        }
        
        participants = load_participants()
        participants.append(participant)
        save_participants(participants)
        return jsonify({'success': True, 'participant': participant}), 201
    except Exception as e:
        logger.error(f'Error adding participant: {e}')
        return jsonify({'error': 'Failed to add participant'}), 500


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
