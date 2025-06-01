from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from .config import config_by_name # This imports your config_by_name dictionary

# Initialize extensions globally but without an app instance yet
db = SQLAlchemy()
migrate = Migrate()
cors = CORS() # Initialize CORS instance

def create_app(config_name='default'): # config_name can be 'dev', 'prod', 'test'
    """
    Application factory function.
    """
    app = Flask(__name__)
    
    # Load configuration using the name (e.g., 'dev', 'prod')
    current_config_object = config_by_name[config_name]
    app.config.from_object(current_config_object)

    # --- DEBUG PRINT for SQLALCHEMY_DATABASE_URI ---
    # This will show the exact URI that Flask is configured with
    print(f"DEBUG [__init__.py]: SQLALCHEMY_DATABASE_URI from Flask app.config: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    # --- END DEBUG PRINT ---

    # Call init_app on the Config class itself if you have app-specific config logic there
    if hasattr(current_config_object, 'init_app') and callable(getattr(current_config_object, 'init_app')):
        current_config_object.init_app(app) # Pass the app instance to the config's init_app

    # Initialize extensions with the app instance
    # For this "fresh start" test, we are NOT passing engine_options to db.init_app()
    # We rely solely on the SQLALCHEMY_DATABASE_URI.
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app) # Initialize CORS with the app. You might add specific origins later.

    # Import and Register your Blueprints
    from .routes import main_routes as main_blueprint # Assuming main_routes is your Blueprint in routes.py
    app.register_blueprint(main_blueprint)
    # If you have other blueprints, register them here as well
    # Example: from .api_routes import api_bp
    # app.register_blueprint(api_bp, url_prefix='/api')

    # Ensure models are imported so SQLAlchemy/Migrate knows about them.
    # This is usually done within an app context or after db is initialized.
    with app.app_context():
        from . import models # This will execute models.py and register your models

    return app