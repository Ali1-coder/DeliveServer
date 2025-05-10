from flask import request, jsonify,url_for
from flask_restful import Resource, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Parcel, TrackingUpdate, Rating,Driver
from helpers import assign_driver_automatically
from decorators import admin_required
from user_schema import UserUpdateSchema
from datetime import datetime
from marshmallow import ValidationError
from extensions import db

class AdminUserDetail(Resource):
    @jwt_required()
    @admin_required
    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        return user.to_dict()

    @jwt_required()
    @admin_required
    def patch(self, user_id):
        user = User.query.get_or_404(user_id)
        data = UserUpdateSchema().load(request.get_json())  # New schema for updates
        # Validate and update user
        return user.to_dict()

    @jwt_required()
    @admin_required
    def delete(self, user_id):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {'message': 'User deleted'}, 200

# User Detail Resource (GET, PATCH, DELETE)
class UserDetail(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if not user:
            abort(404, message='User not found')
        return {
            'user': user.to_dict(),
            'links': {
                'parcels': url_for('user.parcels', _external=True)
            }
        }, 200

    @jwt_required()
    def patch(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if not user:
            abort(404, message='User not found')

        data = UserUpdateSchema().load(request.get_json() or {})

        new_email = data.get('email')
        if new_email and User.query.filter(User.email == new_email, User.id != user.id).first():
            raise ValidationError('Email already exists.')
        for attr, value in data.items():
            if hasattr(user, attr):
                setattr(user, attr, value)
        db.session.commit()
        return user.to_dict(), 200
    
    @jwt_required()
    def delete(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if not user:
            abort(404, message='User not found')

        db.session.delete(user)
        db.session.commit()
        return {'message': 'User deleted successfully'}, 200

# User Parcels Resource (GET, POST)
class UserParcels(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        parcels = Parcel.query.filter_by(user_id=user.id).all()
        return jsonify([parcel.to_dict() for parcel in parcels])

    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        data = request.get_json()

        required_fields = ['weight', 'pickup_address', 'destination', 'recipient_name', 'recipient_phone']
        for field in required_fields:
            if field not in data:
                return {'message': f'{field} is required.'}, 400

        new_parcel = Parcel(
            
            user_id=user.id,
            weight=data['weight'],
            # payment_status='pending',
            status='pending',
            description=data.get('description'),
            pickup_address=data['pickup_address'],
            destination=data['destination'],
            present_location=data['pickup_address'],
            pickup_lat=data.get('pickup_lat'),
            pickup_lon=data.get('pickup_lon'),
            destination_lat=data.get('destination_lat'),
            destination_lon=data.get('destination_lon'),
            recipient_name=data['recipient_name'],
            recipient_phone=data['recipient_phone'],
        )

        new_parcel.driver_id = assign_driver_automatically()
        db.session.add(new_parcel)
        db.session.commit()
        return new_parcel.to_dict(), 201

# Parcel Detail (GET, PATCH, DELETE)
class ParcelDetail(Resource):
    @jwt_required()
    def get(self, parcel_id):
        parcel = Parcel.query.get(parcel_id)
        if not parcel:
            return {'message': 'Parcel not found'}, 404
        return parcel.to_dict(), 200

    @jwt_required()
    def patch(self, parcel_id):
        parcel = Parcel.query.get(parcel_id)
        if not parcel:
            return {'message': 'Parcel not found'}, 404
        if parcel.status in ('delivered', 'cancelled'):
            abort(400, message ='Cannot modify delivered/cancelled parcel')

        data = request.get_json()
        for attr, value in data.items():
            if hasattr(parcel, attr):
                setattr(parcel, attr, value)
        db.session.commit()
        return parcel.to_dict(), 200

    @jwt_required()
    def delete(self, parcel_id):
        parcel = Parcel.query.get(parcel_id)
        if not parcel:
            return {'message': 'Parcel not found'}, 404
        db.session.delete(parcel)
        db.session.commit()
        return {'message': 'Parcel deleted'}, 200

# Parcel Delivery Confirmation
class ParcelDeliveryConfirm(Resource):
    @jwt_required()
    def post(self, parcel_id):
        parcel = Parcel.query.get(parcel_id)
        if not parcel:
            return {'message': 'Parcel not found'}, 404
        if parcel.status != 'in_transit':
            return {'message': 'Parcel not in transit'}, 400

        parcel.status = 'delivered'
        parcel.present_location = parcel.destination_address
        parcel.delivered_at = datetime.utcnow()
        db.session.commit()
        return {'message': 'Parcel marked as delivered'}, 200

# Parcel Tracking
class ParcelTracking(Resource):
    @jwt_required()
    def get(self, parcel_id):
        current_user = get_jwt_identity()
        parcel = Parcel.query.get(parcel_id)
        if not parcel:
            return {'message': 'Parcel not found'}, 404
        if parcel.user.username != current_user:
            return {'message': 'Unauthorized access'}, 403
        updates = TrackingUpdate.query.filter_by(parcel_id=parcel_id).all()
        return jsonify([u.to_dict() for u in updates])

# Parcel Rating
class ParcelRating(Resource):
    @jwt_required()
    def post(self, parcel_id):
        data = request.get_json()
        rating = Rating(
            parcel_id=parcel_id,
            stars=data['stars'],
            comment=data.get('comment')
        )
        db.session.add(rating)
        db.session.commit()
        return rating.to_dict(), 201

# Driver Rating
class DriverRating(Resource):
    @jwt_required()
    def post(self, driver_id):
        driver = Driver.query.get(driver_id)
        if not driver:
            return {'message': 'Driver not found'}, 404
        data = request.get_json()
        rating = Rating(
            driver_id=driver_id,
            stars=data['stars'],
            comment=data.get('comment')
        )
        db.session.add(rating)
        db.session.commit()
        return rating.to_dict(), 201

# # Parcel Payment
# class ParcelPayment(Resource):
#     @jwt_required()
#     def post(self, parcel_id):
#         current_user = get_jwt_identity()
#         parcel = Parcel.query.get(parcel_id)

#         if not parcel:
#             return {'message': 'Parcel not found'}, 404
#         if parcel.user.username != current_user:
#             return {'message': 'Unauthorized access'}, 403

#         if parcel.payment_status != 'pending':
#             return {'message': 'Payment not allowed for this parcel state'}, 400

#         data = request.get_json()
#         payment = Payment(
#             parcel_id=parcel.id,
#             amount=data['amount'],
#             status='paid'
#         )
#         db.session.add(payment)
#         parcel.payment_status = 'paid'
#         db.session.commit()
#         return {'message': 'Payment successful', 'payment': payment.to_dict()}, 201

# Admin: View All Parcels
class AdminAllParcels(Resource):
    @jwt_required()
    @admin_required
    def get(self):
        parcels = Parcel.query.all()
        return jsonify([p.to_dict() for p in parcels])

# Admin: Users
class AdminUsers(Resource):
    @jwt_required()
    @admin_required
    def get(self):
        users = User.query.all()
        return jsonify([u.to_dict() for u in users])

# Admin: Ratings
class AdminRatings(Resource):
    @jwt_required()
    @admin_required
    def get(self):
        ratings = Rating.query.all()
        return jsonify([r.to_dict() for r in ratings])

# Admin: Tracking Updates
class AdminTrackingUpdates(Resource):
    @jwt_required()
    @admin_required
    def post(self, parcel_id):
        data = request.get_json()
        update = TrackingUpdate(
            parcel_id=parcel_id,
            location=data['location'],
            status=data['status']
        )
        db.session.add(update)
        db.session.commit()
        return update.to_dict(), 201

# Driver Detail (GET, PATCH, DELETE)
class DriverDetail(Resource):
    @jwt_required()
    def get(self, driver_id):
        driver = Driver.query.get(driver_id)
        if not driver:
            return {'message': 'Driver not found'}, 404
        return driver.to_dict(), 200

    @jwt_required()
    def patch(self, driver_id):
        driver = Driver.query.get(driver_id)
        if not driver:
            return {'message': 'Driver not found'}, 404

        data = request.get_json()
        driver.name = data.get('name', driver.name)
        driver.phone_number = data.get('phone_number', driver.phone_number)
        db.session.commit()
        return driver.to_dict(), 200

    @jwt_required()
    def delete(self, driver_id):
        driver = Driver.query.get(driver_id)
        if not driver:
            return {'message': 'Driver not found'}, 404

        db.session.delete(driver)
        db.session.commit()
        return {'message': 'Driver deleted successfully'}, 200