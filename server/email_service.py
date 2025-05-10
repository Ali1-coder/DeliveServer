import time
from flask import current_app, render_template_string
from flask_mail import Message
from smtplib import SMTPException 
from extensions import mail
from flask import  current_app, render_template_string
from email_validator import validate_email, EmailNotValidError

VERIFICATION_TEMPLATE = """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #333; border-bottom: 2px solid #00CCBC; padding-bottom: 10px;">
        Welcome to Deliveroo!
    </h2>
    <p style="line-height: 1.6; color: #444; margin: 20px 0;">
        Thank you for signing up. Please verify your email address by clicking the link below:
    </p>
    <p style="text-align: center; margin: 30px 0;">
        <a href="{{ verification_url|safe }}" 
           style="display: inline-block; 
                  padding: 12px 25px;
                  background-color: #00CCBC; 
                  color: white; 
                  text-decoration: none; 
                  border-radius: 5px;
                  font-weight: bold;">
            Verify Email Address
        </a>
    </p>
    <p style="color: #666; font-size: 0.9em;">
        If the button doesn't work, copy and paste this URL into your browser:<br>
        <code style="word-break: break-all; display: inline-block; margin-top: 8px;">
            {{ verification_url|safe }}
        </code>
    </p>
    <p style="color: #999; font-size: 0.85em; margin-top: 25px;">
        This link will expire in 24 hours.
    </p>
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #777;">
            Best regards,<br>
            <strong>The Deliveroo Team</strong>
        </p>
    </footer>
</div>"""  
# Define template once

PASSWORD_RESET_TEMPLATE = """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #333; border-bottom: 2px solid #00CCBC; padding-bottom: 10px;">
        Password Reset Request
    </h2>
    <p style="line-height: 1.6; color: #444; margin: 20px 0;">
        We received a request to reset your password. Click the link below to set a new password:
    </p>
    <p style="text-align: center; margin: 30px 0;">
        <a href="{{ reset_url|safe }}" 
           style="display: inline-block; 
                  padding: 12px 25px;
                  background-color: #00CCBC; 
                  color: white; 
                  text-decoration: none; 
                  border-radius: 5px;
                  font-weight: bold;">
            Reset Password
        </a>
    </p>
    <p style="color: #666; font-size: 0.9em;">
        If the button doesn't work, copy and paste this URL into your browser:<br>
        <code style="word-break: break-all; display: inline-block; margin-top: 8px;">
            {{ reset_url|safe }}
        </code>
    </p>
    <p style="color: #999; font-size: 0.85em; margin-top: 25px;">
        This link will expire in 1 hour.
    </p>
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 30px;">
        <p style="color: #666; margin: 0; font-size: 0.9em;">
            If you didn't request this password reset, please ignore this email. 
            Your account remains secure.
        </p>
    </div>
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #777;">
            Best regards,<br>
            <strong>The Deliveroo Team</strong>
        </p>
    </footer>
</div>"""

def _send_email(email, subject, template, **context):
    """Helper for sending emails with retries"""
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        current_app.logger.warning("Invalid email format detected (redacted)")
        return False

    required_configs = ['FRONTEND_URL', 'MAIL_DEFAULT_SENDER']
    for config_key in required_configs:
        if not current_app.config.get(config_key):
            current_app.logger.error(f"Missing {config_key} in config")
            return False

    try:
        msg = Message(
            subject=subject,
            recipients=[email],
            html=render_template_string(template, **context),
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Retry logic
        max_retries = 2
        for attempt in range(max_retries):
            try:
                mail.send(msg)
                current_app.logger.info(f"Email sent successfully to {email[:3]}...")
                return True
            except SMTPException as e:
                if attempt == max_retries - 1:
                    current_app.logger.error(f"Email failed after {max_retries} attempts: {str(e)}")
                    return False
                time.sleep(1)
                
    except Exception as e:
        current_app.logger.error(f"Critical email failure: {str(e)}")
        return False
def send_verification_email(email, token):
    # verification_url = f"{current_app.config['FRONTEND_URL']}/verify-email?token={token}"
    verification_url = f"http://localhost:5000/api/auth/users/verify?token={token}"
    return _send_email(
        email=email,
        subject="Verify Your Deliveroo Account",
        template=VERIFICATION_TEMPLATE,
        verification_url=verification_url
    )

def send_password_reset_email(email, token):
    reset_url = f"{current_app.config['FRONTEND_URL']}/reset-password?token={token}"
    return _send_email(
        email=email,
        subject="Reset Your Deliveroo Password",
        template=PASSWORD_RESET_TEMPLATE,
        reset_url=reset_url
    )

