import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)


def get_jwt_config():
    """Get JWT configuration from environment variables"""
    return {
        'secret_key': os.getenv('SECRET_KEY', 'fallback-secret-key'),
        'access_expires_min': int(os.getenv('JWT_EXPIRES_MIN', 60)),
        'refresh_expires_min': int(os.getenv('JWT_REFRESH_MIN', 1440))
    }


def generate_tokens(username):
    """Generate access and refresh tokens for a user"""
    config = get_jwt_config()

    now = datetime.utcnow()
    access_expires = now + timedelta(minutes=config['access_expires_min'])
    refresh_expires = now + timedelta(minutes=config['refresh_expires_min'])

    access_token = jwt.encode(
        {
            'username': username,
            'exp': access_expires,
            'iat': now,
            'type': 'access'
        },
        config['secret_key'],
        algorithm='HS256'
    )

    refresh_token = jwt.encode(
        {
            'username': username,
            'exp': refresh_expires,
            'iat': now,
            'type': 'refresh'
        },
        config['secret_key'],
        algorithm='HS256'
    )

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': config['access_expires_min'] * 60  # seconds
    }


def verify_token(token):
    """Verify and decode a JWT token"""
    try:
        config = get_jwt_config()
        payload = jwt.decode(token, config['secret_key'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def jwt_required(f):
    """Decorator to require JWT authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None

        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Add user info to request context
        request.current_user = payload
        return f(*args, **kwargs)

    return decorated_function


def refresh_token(refresh_token):
    """Generate new access token using refresh token"""
    payload = verify_token(refresh_token)
    if not payload or payload.get('type') != 'refresh':
        return None

    return generate_tokens(payload['username'])
