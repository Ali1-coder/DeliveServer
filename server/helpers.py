from flask import jsonify
from models import  Driver
from extensions import db

def success_response(data, status_code=200):
    return jsonify({
        'status': 'success',
        'data': data
    }), status_code

def error_response(message, status_code=400):
    return jsonify({
        'status': 'error',
        'message': message
    }), status_code

def validate_required_fields(data, required_fields):
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return error_response(f'Missing fields: {", ".join(missing_fields)}', 400)
    return None 


def format_date(date_obj):
    return date_obj.strftime('%Y-%m-%d %H:%M:%S') if date_obj else None


def assign_driver_automatically():
    available_driver = Driver.query.filter_by(is_available=True).first()
    if available_driver:
        available_driver.is_available = False
        db.session.commit()
        return available_driver.id  
    return None


def validate_payment(data):
    if 'amount' not in data or 'status' not in data:
        return error_response('Payment amount and status are required', 400)
    if data['status'] not in ['Pending', 'Completed', 'Failed']:
        return error_response('Invalid payment status', 400)
    return None  