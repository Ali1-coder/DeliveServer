from resources import (
    UserDetail, UserParcels, ParcelDetail,
    ParcelTracking, ParcelRating, DriverRating, AdminAllParcels,
    AdminUsers, AdminRatings, AdminTrackingUpdates, DriverDetail
)
from auth import api,UserRegisterResource,EmailVerificationResource,UserLoginResource,LogoutResource,PasswordResetRequestResource,PasswordResetConfirmResource,ResendVerificationResource


def register_routes():
    api.add_resource(UserRegisterResource, '/users')
    api.add_resource(EmailVerificationResource, '/users/verify')
    api.add_resource(UserLoginResource, '/sessions')
    api.add_resource(LogoutResource, '/sessions')
    api.add_resource(PasswordResetRequestResource, '/password-reset')
    api.add_resource(PasswordResetConfirmResource, '/password-reset/confirm')
    api.add_resource(ResendVerificationResource, '/users/resend-verification')

    api.add_resource(UserDetail, '/user')
    api.add_resource(UserParcels, '/user/parcels')
    api.add_resource(ParcelDetail, '/parcel/<int:parcel_id>')
    api.add_resource(ParcelTracking, '/parcel/<int:parcel_id>/tracking')
    api.add_resource(ParcelRating, '/parcel/<int:parcel_id>/rating')
    api.add_resource(DriverRating, '/driver/<int:driver_id>/rating')
    api.add_resource(AdminAllParcels, '/admin/parcels')
    api.add_resource(AdminUsers, '/admin/users')
    api.add_resource(AdminRatings, '/admin/ratings')
    api.add_resource(AdminTrackingUpdates, '/admin/parcel/<int:parcel_id>/tracking')
    api.add_resource(DriverDetail, '/driver/<int:driver_id>')