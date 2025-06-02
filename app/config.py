import os
from dotenv import load_dotenv

# --- Path Setup for .env (primarily for local development) ---
current_script_path = os.path.abspath(__file__)
app_dir = os.path.dirname(current_script_path)
backend_root_dir = os.path.dirname(app_dir) # This is your 'backend' folder
dotenv_path = os.path.join(backend_root_dir, '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    # Conditional print for development
    if os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == '1':
        print(f"DEBUG [config.py]: Successfully loaded .env file from: {dotenv_path}")
else:
    # This is expected on Render, as .env is not deployed
    if os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == '1': # Or check if not 'production'
        print(f"INFO [config.py]: .env file NOT FOUND at: {dotenv_path}. Relying on environment variables set by the platform or defaults.")

DB_URL_FROM_ENV = os.getenv('DB_URL')
DB_HOST_FROM_ENV = os.getenv('DB_HOST') # Used to determine if PostgreSQL specific vars are set

if os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == '1':
    print(f"DEBUG [config.py]: Value of os.getenv('DB_URL') after load_dotenv() is: {DB_URL_FROM_ENV}")
    print(f"DEBUG [config.py]: Value of os.getenv('DB_HOST') is: {DB_HOST_FROM_ENV}")

class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-very-secure-default-dev-secret-key-please-change-me-for-prod')
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
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(backend_root_dir, 'default_app_sqlite.db')

    @staticmethod
    def init_app(app):
        is_production = app.config.get('ENV') == 'production' or not app.config.get('DEBUG', False)
        
        if not app.config.get('SECRET_KEY') or \
           app.config['SECRET_KEY'] == 'a-very-secure-default-dev-secret-key-please-change-me-for-prod':
            log_message = "CRITICAL: Production SECRET_KEY is not set or is using a weak default!" if is_production else \
                          "WARNING: SECRET_KEY is not set or is using a weak default. Please set a strong SECRET_KEY for production."
            if hasattr(app, 'logger'): app.logger.warning(log_message)
            else: print(log_message)
        
        if not app.config.get('ENCRYPTION_KEY'):
            log_message = "CRITICAL: Production ENCRYPTION_KEY is not set!" if is_production else \
                          "WARNING: ENCRYPTION_KEY not set. Fingerprint data encryption will be insecure or may fail."
            if hasattr(app, 'logger'): app.logger.warning(log_message)
            else: print(log_message)
        
        if app.debug or is_production: # Always log DB URI in production for clarity during setup
            if hasattr(app, 'logger'):
                app.logger.info(f"INFO: Flask App Initialized. Using SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
            else:
                print(f"INFO: Flask App Initialized. Using SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")


class DevelopmentConfig(Config):
    DEBUG = True
    # Use DB_URL from .env for local dev, defaulting to dev_app.db in backend root
    SQLALCHEMY_DATABASE_URI = os.getenv('DB_URL') or \
                              'sqlite:///' + os.path.join(backend_root_dir, 'dev_app.db')
    # SQLALCHEMY_ECHO = True 

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DB_URL') or \
                              'sqlite:///' + os.path.join(backend_root_dir, 'test_app.db')
    WTF_CSRF_ENABLED = False 
    SECRET_KEY = os.getenv('TEST_SECRET_KEY', 'test-secret-key')
    ENCRYPTION_KEY = os.getenv('TEST_ENCRYPTION_KEY', Config.ENCRYPTION_KEY or 'test_default_encryption_key_32b_placeholder')

class ProductionConfig(Config):
    DEBUG = False
    # For SQLite testing on Render's ephemeral disk:
    # This file will be created in the root of your app directory on Render
    # (relative to where Gunicorn/Flask is run, typically /opt/render/project/src/ on Render).
    # The 'instance' folder might be more standard if your app factory configures an instance_path.
    # For simplicity and directness for ephemeral SQLite on Render:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///render_prod_app.db' 
    
    # This print will execute when config.py is imported, useful for build logs on Render
    print(f"INFO [ProductionConfig]: Using fixed SQLite URI for production/Render: {SQLALCHEMY_DATABASE_URI}")

    # Ensure critical environment variables are set for production
    # These checks run when ProductionConfig class is defined.
    if not os.getenv('SECRET_KEY') or os.getenv('SECRET_KEY') == 'a-very-secure-default-dev-secret-key-please-change-me-for-prod':
        print("CRITICAL_WARNING [ProductionConfig]: Production SECRET_KEY is not set or is using the default development key!")
    if not os.getenv('ENCRYPTION_KEY'):
        print("CRITICAL_WARNING [ProductionConfig]: Production ENCRYPTION_KEY is not set!")
    # Add more checks for other critical os.getenv values here if needed for production


config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    prod=ProductionConfig,
    default=DevelopmentConfig 
)

# --- Fernet Cipher Initialization ---
_fernet_cipher = None
_env_encryption_key = os.getenv('ENCRYPTION_KEY')
if os.getenv('FLASK_CONFIG') == 'test' and os.getenv('TEST_ENCRYPTION_KEY'):
    _env_encryption_key = os.getenv('TEST_ENCRYPTION_KEY')

if _env_encryption_key:
    try:
        from cryptography.fernet import Fernet
        _fernet_cipher = Fernet(_env_encryption_key.encode())
        # Conditional print for development
        if os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == '1':
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