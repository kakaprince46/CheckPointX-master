import os
from dotenv import load_dotenv

# --- Path Setup for .env (primarily for local development) ---
current_script_path = os.path.abspath(__file__)
app_dir = os.path.dirname(current_script_path)
backend_root_dir = os.path.dirname(app_dir) # This is your 'backend' folder
dotenv_path = os.path.join(backend_root_dir, '.env')

# Load .env only if it exists (it won't exist in production on Render typically)
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    # print(f"DEBUG [config.py]: Successfully loaded .env file from: {dotenv_path}") # Less verbose for prod
else:
    print(f"INFO [config.py]: .env file NOT FOUND at: {dotenv_path}. Relying on environment variables set by the platform.")

# These are primarily for local dev or if config builds URI from parts
DB_URL_FROM_ENV = os.getenv('DB_URL')
DB_HOST_FROM_ENV = os.getenv('DB_HOST')

# Print these only if FLASK_ENV is development or FLASK_DEBUG is true
if os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == '1':
    print(f"DEBUG [config.py]: Value of os.getenv('DB_URL') after load_dotenv() is: {DB_URL_FROM_ENV}")
    print(f"DEBUG [config.py]: Value of os.getenv('DB_HOST') is: {DB_HOST_FROM_ENV}")

class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv('SECRET_KEY') # Production should FAIL if not set, see ProductionConfig
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    RESEND_API_KEY = os.getenv('RESEND_API_KEY')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
    AFRICASTALKING_USERNAME = os.getenv('AFRICASTALKING_USERNAME')
    AFRICASTALKING_API_KEY = os.getenv('AFRICASTALKING_API_KEY')
    FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')
    FIREBASE_AUTH_DOMAIN = os.getenv('FIREBASE_AUTH_DOMAIN')
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')

    # Default SQLALCHEMY_DATABASE_URI (will be overridden by specific configs)
    # This ensures the attribute exists on the base Config class.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(backend_root_dir, 'default_app_sqlite.db')


    @staticmethod
    def init_app(app):
        # Check for critical missing configurations, especially for production
        if app.config.get('ENV') == 'production': # or app.config.get('DEBUG') is False
            if not app.config.get('SECRET_KEY') or app.config['SECRET_KEY'] == 'a-very-secure-default-dev-secret-key-please-change-me-for-prod':
                app.logger.critical("CRITICAL: Production SECRET_KEY is not set or is using a weak default!")
            if not app.config.get('ENCRYPTION_KEY'):
                app.logger.critical("CRITICAL: Production ENCRYPTION_KEY is not set!")
            # For the new setup, DATABASE_URL check from Render is not primary for SQLite
            # if not app.config.get('DATABASE_URL') and not ('sqlite:///' in app.config.get('SQLALCHEMY_DATABASE_URI', '')):
            # app.logger.critical("CRITICAL: Production DATABASE_URL for PostgreSQL is not set!")
            if 'sqlite:///render_app.db' not in app.config.get('SQLALCHEMY_DATABASE_URI', ''):
                 # This condition might need adjustment based on how you verify the forced SQLite path
                 app.logger.info(f"INFO: Production is set to use specific SQLite path: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
            # Add more critical checks for other API keys if needed for production
        
        # Log the database URI being used, especially in development
        if app.debug:
            app.logger.info(f"INFO: Flask App Initialized. Using SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DB_URL') or \
                              'sqlite:///' + os.path.join(backend_root_dir, 'dev_app.db') # Specific for dev
    # SQLALCHEMY_ECHO = True 

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DB_URL') or \
                              'sqlite:///' + os.path.join(backend_root_dir, 'test_app.db')
    WTF_CSRF_ENABLED = False 
    SECRET_KEY = os.getenv('TEST_SECRET_KEY', 'test-secret-key')
    ENCRYPTION_KEY = os.getenv('TEST_ENCRYPTION_KEY', Config.ENCRYPTION_KEY or 'test_default_encryption_key_32b_placeholder')

# --- Updated ProductionConfig ---
class ProductionConfig(Config):
    DEBUG = False
    
    # For this SQLite test on Render, we will use a fixed relative path.
    # This ensures flask db upgrade and the running app use the SAME file.
    # The file will be in the root of your backend project on Render.
    # The original backend_root_dir points to the 'backend' folder.
    # So, 'sqlite:///render_app.db' would be relative to where the script is run from.
    # If Render runs from 'backend' folder, then 'render_app.db' will be in 'backend/render_app.db'
    # If Render runs from project root (containing 'backend'), then 'sqlite:///backend/render_app.db' might be needed
    # For simplicity and assuming Render runs from within the 'backend' directory or similar:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///render_app.db' 
                                    # Changed name for clarity and to ensure it's fresh
    
    print(f"INFO [ProductionConfig]: Using SQLite database URI: {SQLALCHEMY_DATABASE_URI}")

    # Ensure critical environment variables are set
    # Using os.getenv() directly here as per the update request
    if not os.getenv('SECRET_KEY') or os.getenv('SECRET_KEY') == 'a-very-secure-default-dev-secret-key-please-change-me-for-prod':
        print("CRITICAL_WARNING [ProductionConfig]: Production SECRET_KEY is not set or is using the default development key!")
    if not os.getenv('ENCRYPTION_KEY'):
        print("CRITICAL_WARNING [ProductionConfig]: Production ENCRYPTION_KEY is not set!")
    # Add other critical checks if needed
# --- End of Updated ProductionConfig ---

config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    prod=ProductionConfig,
    default=DevelopmentConfig 
)

# --- Fernet Cipher Initialization ---
_fernet_cipher = None
_env_encryption_key = os.getenv('ENCRYPTION_KEY')
# For TestingConfig, if FLASK_CONFIG=test, it might override ENCRYPTION_KEY from .env if TEST_ENCRYPTION_KEY is set
if os.getenv('FLASK_CONFIG') == 'test' and os.getenv('TEST_ENCRYPTION_KEY'):
    _env_encryption_key = os.getenv('TEST_ENCRYPTION_KEY')

if _env_encryption_key:
    try:
        from cryptography.fernet import Fernet
        _fernet_cipher = Fernet(_env_encryption_key.encode())
        if os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == '1': # Only print in dev
            print("DEBUG [config.py]: Fernet cipher initialized successfully.")
    except ImportError:
        print("WARNING [config.py]: 'cryptography' library not installed. Fingerprint data encryption will not work.")
        _fernet_cipher = None
    except Exception as e:
        print(f"WARNING [config.py]: Invalid ENCRYPTION_KEY format or other Fernet error. Could not initialize Fernet cipher. Error: {e}")
        _fernet_cipher = None 
else:
    if os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == '1':
        print("DEBUG [config.py]: ENCRYPTION_KEY not found in environment, Fernet cipher not initialized.")

def get_fernet_cipher():
    global _fernet_cipher 
    return _fernet_cipher