from flask import Blueprint, request, current_app
from flask_restful import Api, Resource
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from extensions import db
from models import User
from user_schema import UserRegisterSchema,UserLoginSchema,PasswordResetRequestSchema,UserBaseSchema
from email_service import send_verification_email, send_password_reset_email
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask_cors import cross_origin
from decorators import validate_json,generate_secure_token,generate_token,token_required,blacklist_token

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
api = Api(auth_bp)

class UserRegisterResource(Resource):
    @validate_json(UserRegisterSchema)
    def post(self, validated_data):
        if validated_data['password'] != validated_data['confirm_password']:
            return {'message': 'Passwords do not match'}, 400
        if User.query.filter_by(email=validated_data['email']).first():
            return {'message': 'User already exists with this email'}, 409
        try:
            hashed = generate_password_hash(validated_data['password'])
            token = generate_secure_token()
            user = User(
                first_name=validated_data['first_name'],
                second_name=validated_data['second_name'],
                username=validated_data['username'],
                email=validated_data['email'],
                password_hash=hashed,
                verification_token=token,
                token_expiry=datetime.utcnow() + timedelta(hours=24),
                is_active=False
            )
            db.session.add(user)
            # send email
            sent = send_verification_email(user.email, token)
            if not sent:
                db.session.rollback()
                return {'message': 'Registration failed due to email service issue'}, 500
            db.session.commit()
            return {
                'message': 'User registered. Check email to verify.',
                'user_id': user.id
            }, 201
        except IntegrityError:
            db.session.rollback()
            return {'message': 'Username or email already exists'}, 409
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Register error: {e}")
            return {'message': 'An error occurred during registration'}, 500

class EmailVerificationResource(Resource):
    @cross_origin()
    def options(self):
        return {'message': 'CORS preflight success'}, 200

    @cross_origin()
    def get(self):
        token = request.args.get('token')
        return self._verify(token)

    @cross_origin()
    def post(self):
        data = request.get_json() or {}
        token = data.get('token')
        return self._verify(token)

    def _verify(self, token):
        if not token or not isinstance(token, str):
            return {'message': 'Missing or invalid verification token'}, 400
        try:
            user = User.query.filter_by(verification_token=token).first()
            if not user:
                return {'message': 'Invalid token'}, 400
            user.is_active = True
            user.verification_token = None
            db.session.commit()
            return {'message': 'Email verified successfully'}, 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Verify error: {e}")
            return {'message': 'An error occurred during email verification'}, 500

class UserLoginResource(Resource):
    @validate_json(UserLoginSchema)
    def post(self, validated_data):
        try:
            user = User.query.filter_by(email=validated_data['email']).first()
            if not user or not user.check_password(validated_data['password']):
                return {'message': 'Invalid email or password'}, 401
            if not user.is_active:
                return {'message': 'Please verify your email before logging in'}, 401
            token = generate_token(user.id)
            result = {
                'message': 'Login successful',
                'token': token,
                'user': UserBaseSchema().dump(user)
            }
            result['redirect'] = '/admin-dashboard' if user.is_admin else '/dashboard'
            return result, 200
        except Exception as e:
            current_app.logger.error(f"Login error: {e}")
            return {'message': 'An error occurred during login'}, 500

class LogoutResource(Resource):
    @token_required
    def delete(self, current_user):
        auth = request.headers.get('Authorization', '')
        jti = auth.split()[1]
        try:
            blacklist_token(jti)
            return {'message': 'Successfully logged out'}, 200
        except Exception as e:
            current_app.logger.error(f"Logout error: {e}")
            return {'message': 'An error occurred during logout'}, 500


        
class PasswordResetRequestResource(Resource):
    @validate_json(PasswordResetRequestSchema)
    def post(self, validated_data):
        try:
            email = validated_data['email'].lower().strip()  # Normalize email
            user = User.query.filter(User.email.ilike(email)).first()  # Case-insensitive search

            if not user:
                # Always return same message for security
                current_app.logger.info(f"Password reset request for non-existent email: {email}")
                return {'message': 'If your email is registered, you will receive a password reset link'}, 200

            # Generate unique token with collision check
            max_attempts = 3
            for _ in range(max_attempts):
                token = generate_secure_token()
                if not User.query.filter_by(reset_token=token).first():
                    break
            else:
                current_app.logger.error("Failed to generate unique reset token after 3 attempts")
                return {'message': 'If your email is registered, you will receive a password reset link'}, 200

            # Update user with new token and expiry
            user.reset_token = token
            user.token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.add(user)
            db.session.flush()  # Write to DB without commit

            # Attempt email send
            if not send_password_reset_email(user.email, token):
                db.session.rollback()
                current_app.logger.error(f"Password reset email failed to send for {email}")
                return {'message': 'If your email is registered, you will receive a password reset link'}, 200

            db.session.commit()
            current_app.logger.info(f"Password reset token generated for {email}")
            return {'message': 'If your email is registered, you will receive a password reset link'}, 200

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during password reset request: {str(e)}")
            return {'message': 'If your email is registered, you will receive a password reset link'}, 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error during password reset request: {str(e)}")
            return {'message': 'If your email is registered, you will receive a password reset link'}, 200

class PasswordResetConfirmResource(Resource):
    def post(self):
        try:
            data = request.get_json() or {}
            token = data.get('token')
            pwd = data.get('password')
            confirm = data.get('confirm_password')
            if not token or not pwd or not confirm:
                return {'message': 'Token, password, and confirm password are required'}, 400
            user = User.query.filter_by(reset_token=token).first()
            if not user or not user.token_expiry or user.token_expiry < datetime.utcnow():
                return {'message': 'Invalid or expired token'}, 400
            if pwd != confirm:
                return {'message': 'Passwords do not match'}, 400
            user.password_hash = generate_password_hash(pwd)
            user.reset_token = None
            user.token_expiry = None
            db.session.commit()
            return {'message': 'Password updated successfully'}, 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Password reset error: {e}")
            return {'message': 'An error occurred during password reset'}, 500

class ResendVerificationResource(Resource):
    @validate_json(PasswordResetRequestSchema)
    def post(self, validated_data):
        try:
            user = User.query.filter_by(email=validated_data['email']).first()
            if not user:
                return {'message': 'If your email is registered, you will receive a verification link'}, 200
            if user.is_active:
                return {'message': 'This account is already verified'}, 400
            token = generate_secure_token()
            user.verification_token = token
            user.token_expiry = datetime.utcnow() + timedelta(hours=24)
            sent = send_verification_email(user.email, token)
            if not sent:
                db.session.rollback()
                return {'message': 'If your email is registered, you will receive a verification link'}, 200
            db.session.commit()
            return {'message': 'If your email is registered, you will receive a verification link'}, 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Resend verification error: {e}")
            return {'message': 'An error occurred during resend verification'}, 500





