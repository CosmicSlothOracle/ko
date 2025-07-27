from config import ALLOWED_EXTENSIONS, ADMIN_USER, UPLOAD_FOLDER, PARTICIPANTS_FILE, BASE_DIR
from flask import Flask, jsonify, request, send_from_directory, make_response, redirect
from flask_cors import CORS
import bcrypt
import os
import json
from werkzeug.utils import secure_filename
from cms import ContentManager
import logging
from config import (
    UPLOAD_FOLDER, PARTICIPANTS_FILE, ADMIN_USER,
    CORS_ORIGINS, MAX_CONTENT_LENGTH, init
)
from database import db_manager
from bson.objectid import ObjectId
from jwt_utils import generate_tokens, jwt_required, refresh_token

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Configure CORS more explicitly
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

# Import path constants from config

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

# Import admin user from config


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
    """Load participants from database or file"""
    return db_manager.get_participants()


def save_participants(participants):
    """Save participants to database or file"""
    # This function is kept for compatibility but uses database manager
    for participant in participants:
        db_manager.save_participant(participant)


@app.route('/api/health', methods=['GET'])
def health():
    try:
        # Check if we can read participants file
        participants = load_participants()
        # Check if uploads directory exists
        uploads_exist = os.path.exists(UPLOAD_FOLDER)

        # MongoDB connectivity check
        mongo_connected = False
        gridfs_available = False
        if db_manager.connected:
            try:
                # Ping MongoDB
                db_manager.client.admin.command("ping")
                mongo_connected = True
                # Check GridFS availability
                gridfs_available = db_manager.fs is not None
            except Exception as e:
                logger.warning(f"MongoDB health check failed: {e}")

        return jsonify({
            'status': 'healthy',
            'participants_count': len(participants),
            'uploads_directory': uploads_exist,
            'mongodb_connected': mongo_connected,
            'gridfs_available': gridfs_available,
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
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username == ADMIN_USER['username'] and bcrypt.checkpw(password.encode(), ADMIN_USER['password_hash']):
        # Generate JWT tokens
        tokens = generate_tokens(username)
        return jsonify({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_in': tokens['expires_in'],
            'user': username
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/api/banners', methods=['POST'])
@jwt_required
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

        # Prefer GridFS when available
        if db_manager.connected:
            try:
                file_id = db_manager.store_file(file.read(), filename)
                logger.info(
                    f'Stored file {filename} in GridFS with id {file_id}')
                url = f'/api/files/{file_id}'
                return jsonify({'url': url, 'file_id': file_id, 'filename': filename}), 201
            except Exception as e:
                logger.error(f'Error saving file to GridFS: {str(e)}')
                return jsonify({'error': f'Failed to save file to database: {str(e)}'}), 500

        # --- Fallback: save to local disk ---
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        logger.info(f'Saving file to: {save_path}')
        try:
            file.seek(0)
            file.save(save_path)
            url = f'/api/uploads/{filename}'
            return jsonify({'url': url, 'filename': filename}), 201
        except Exception as e:
            logger.error(f'Error saving file: {str(e)}')
            return jsonify({'error': f'Failed to save file: {str(e)}'}), 500

    logger.error('Invalid file type')
    return jsonify({'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400


@app.route('/api/banners', methods=['GET'])
def list_banners():
    # Prefer GridFS when available
    if db_manager.connected:
        try:
            files = db_manager.fs.find()
            urls = [f'/api/files/{str(file._id)}' for file in files]
            return jsonify({'banners': urls}), 200
        except Exception as e:
            logger.error(f'Error listing GridFS files: {str(e)}')
            # fall through to disk fallback

    files = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)]
    urls = [f'/api/uploads/{f}' for f in files]
    return jsonify({'banners': urls}), 200


@app.route('/api/banners/<identifier>', methods=['DELETE'])
@jwt_required
def delete_banner(identifier):
    # If identifier looks like ObjectId (24 hex chars), attempt GridFS
    if len(identifier) == 24 and db_manager.connected:
        try:
            result = db_manager.fs.delete(ObjectId(identifier))
            return jsonify({'success': True, 'file_id': identifier}), 200
        except Exception as e:
            logger.error(f'Error deleting GridFS file: {str(e)}')
            return jsonify({'error': 'File not found.'}), 404

    # Otherwise treat as filename on disk
    filename = secure_filename(identifier)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not allowed_file(filename):
        return jsonify({'error': 'Invalid file type.'}), 400
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'success': True, 'filename': filename}), 200
    else:
        return jsonify({'error': 'File not found.'}), 404


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

        # Set content type for PNG files
        if filename.lower().endswith('.png'):
            response.headers['Content-Type'] = 'image/png'

        return response
    except Exception as e:
        logger.error(f'Error serving file {filename}: {str(e)}')
        return jsonify({'error': f'Error serving file: {str(e)}'}), 500


@app.route('/api/files/<file_id>')
def get_file(file_id):
    """Serve files stored in GridFS."""
    if not db_manager.connected:
        return jsonify({'error': 'Database not available'}), 503
    try:
        grid_out = db_manager.fs.get(ObjectId(file_id))
        data = grid_out.read()
        response = make_response(data)
        response.headers['Content-Type'] = 'image/png'
        return response
    except Exception as e:
        logger.error(f'Error retrieving file {file_id}: {str(e)}')
        return jsonify({'error': 'File not found'}), 404


@app.route('/api/participants', methods=['POST'])
def add_participant():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')
    banner = data.get('banner')
    if not name:
        return jsonify({'error': 'Name ist erforderlich.'}), 400
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


@app.route('/api/participants', methods=['GET'])
@jwt_required
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
@jwt_required
def get_content(section):
    language = request.args.get('language')
    content = content_manager.get_content(section, language)
    if content:
        return jsonify(content), 200
    return jsonify({'error': 'Content not found'}), 404


@app.route('/api/cms/content/<section>', methods=['POST'])
@jwt_required
def create_content(section):
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    metadata = data.get('metadata', {})

    if not all([title, content]):
        return jsonify({'error': 'Title and content are required'}), 400

    success = content_manager.create_content(section, title, content, metadata)
    if success:
        return jsonify({'success': True, 'section': section}), 201
    return jsonify({'error': 'Failed to create content'}), 500


@app.route('/api/cms/content/<section>', methods=['PUT'])
@jwt_required
def update_content(section):
    data = request.get_json()
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


@app.route('/api/cms/content/<section>/translate/<target_language>', methods=['POST'])
@jwt_required
def translate_content(section, target_language):
    success = content_manager.translate_content(section, target_language)
    if success:
        return jsonify({'success': True, 'section': section, 'language': target_language}), 200
    return jsonify({'error': 'Translation failed'}), 400


@app.route('/api/cms/sections', methods=['GET'])
@jwt_required
def list_sections():
    language = request.args.get('language')
    sections = content_manager.list_sections(language)
    return jsonify({'sections': sections}), 200


@app.route('/api/cms/content/<section>', methods=['DELETE'])
@jwt_required
def delete_content(section):
    language = request.args.get('language')
    success = content_manager.delete_content(section, language)
    if success:
        return jsonify({'success': True}), 200
    return jsonify({'error': 'Content not found'}), 404


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


# JWT Token refresh endpoint
@app.route('/api/refresh', methods=['POST'])
def refresh():
    data = request.get_json()
    refresh_token_value = data.get('refresh_token')

    if not refresh_token_value:
        return jsonify({'error': 'Refresh token is required'}), 400

    tokens = refresh_token(refresh_token_value)
    if not tokens:
        return jsonify({'error': 'Invalid or expired refresh token'}), 401

    return jsonify({
        'access_token': tokens['access_token'],
        'refresh_token': tokens['refresh_token'],
        'expires_in': tokens['expires_in']
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
