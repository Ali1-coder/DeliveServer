import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:Marco2650@localhost:5432/deliveroo'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'bb7523de87660149c8e11db73e41bce56afbbe1ea1324a731c97c415b493911c'  
    JWT_SECRET_KEY = SECRET_KEY  # Use the same key for consistency

    # SMTP Email configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = "deliveroo.notification@gmail.com"
    MAIL_PASSWORD = "vbgv xgyj mzfb rngx"


    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'Deliveroo <deliveroo.notification@gmail.com>')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')






