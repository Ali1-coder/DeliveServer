from flask import Flask
from extensions import db, mail, migrate, jwt, api, cors
from auth import auth_bp
from config import Config

def create_app():
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions with app
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    api.init_app(app)
    cors.init_app(app)

    app.register_blueprint(auth_bp)

    # Register error handlers
    register_error_handlers(app)

    # Import and register routes after app and api are initialized
    from routes import register_routes
    register_routes()

    return app

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found_error(error):
        return {'message': 'Resource not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'message': 'Internal server error'}, 500

# Only run when this script is the main entry point
if __name__ == '__main__':
    app = create_app()
    
    # Create tables if not using Alembic yet
    with app.app_context():
        db.create_all()

    app.run(debug=True)