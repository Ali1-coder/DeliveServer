from functools import wraps
from flask import request, current_app
from datetime import datetime, timedelta
from flask_jwt_extended import get_jwt_identity, jwt_required
from models import User, RevokedToken
from extensions import db
from marshmallow import ValidationError
from flask_restful import Resource
import jwt
import secrets
# -------------------------------------
# Token Utilities
# -------------------------------------
def generate_secure_token():
    return secrets.token_urlsafe(32)

def generate_token(user_id):
    jti = secrets.token_hex(16)  # Unique JWT ID
    payload = {
        'user_id': user_id,
        'jti': jti,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        jti = payload.get('jti')
        if RevokedToken.query.filter_by(jti=jti).first():
            return None
        return payload.get('user_id')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def blacklist_token(jti):
    token = RevokedToken(jti=jti)
    db.session.add(token)
    db.session.commit()
# -------------------------------------
# Decorators
# -------------------------------------
def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if not auth or not auth.startswith('Bearer '):
            return {'message': 'Token is missing'}, 401
        token = auth.split()[1]
        user_id = verify_token(token)
        if not user_id:
            return {'message': 'Token is invalid or expired'}, 401
        current_user = User.query.get(user_id)
        if current_user is None:
            return {'message': 'User not found'}, 404
        return f(current_user, *args, **kwargs)
    return wrapper

def validate_json(schema):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json() or {}
            try:
                validated = schema().load(data)
            except ValidationError as err:
                return err.messages, 400
            
            # Handle self parameter for class-based resources
            if args and isinstance(args[0], Resource):  # Resource instance (self)
                return f(args[0], validated, *args[1:], **kwargs)
            else:
                return f(validated, *args, **kwargs)
            
        return wrapper
    return decorator
def admin_required(f):
    @wraps(f)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if user is None or not user.is_admin:
            return {'message': 'Admin privileges required'}, 403
        return f(*args, **kwargs)
    return wrapper