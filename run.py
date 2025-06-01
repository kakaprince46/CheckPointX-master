import os
from app import create_app # Import the factory function from your 'app' package

# Determine which configuration to use.
# It tries to get FLASK_CONFIG from an environment variable.
# If FLASK_CONFIG is not set, it defaults to 'dev', which will use DevelopmentConfig.
config_name = os.environ.get('FLASK_CONFIG') or 'dev'

# Create an instance of your Flask application using the specified configuration.
app = create_app(config_name)

if __name__ == '__main__':
    # This block runs only when you execute "python run.py" directly.
    # It starts the Flask development server.
    # The 'debug' and 'port' settings are taken from your Flask app's configuration,
    # which were loaded from config.py (and potentially overridden by .env values).
    # Fallback to True for debug and 5000 for port if not found in config.
    app.run(
        debug=app.config.get('DEBUG', True), 
        port=int(app.config.get('PORT', 5000)) # Ensure port is an integer
    )