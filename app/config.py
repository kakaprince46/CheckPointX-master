import os
from dotenv import load_dotenv

# --- Path Setup for .env (primarily for local development) ---
current_script_path = os.path.abspath(__file__)
app_dir = os.path.dirname(current_script_path)
backend_root_dir = os.path.dirname(app_dir)  # This is your 'backend' folder
dotenv_path = os.path.join(backend_root_dir, '.env')

# Load .env only if it exists (it won't exist in production on Render typically)
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    if os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == '1':
        print(f"DEBUG [config.py]: Successfully loaded .env file from: {dotenv_path}")
else:
    if os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == '1':
        print(f"INFO [config.py]: .env file NOT FOUND at: {dotenv_path}. Relying on environment variables set by the platform or defaults.")

DB_URL_FROM_ENV = os.getenv('DB_URL')
DB_HOST_FROM_ENV = os.getenv('DB_HOST')

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
            if hasattr(app, 'logger'):
                app.logger.warning(log_message)
            else:
                print(log_message)

        if not app.config.get('ENCRYPTION_KEY'):
            log_message = "CRITICAL: Production ENCRYPTION_KEY is not set!" if is_production else \
                          "WARNING: ENCRYPTION_KEY not set. Fingerprint data encryption will be insecure or may fail."
            if hasattr(app, 'logger'):
                app.logger.warning(log_message)
            else:
                print(log_message)

        # Log the final DB URI being used by the app
        if hasattr(app, 'logger'):
            app.logger.info(f"INFO: Flask App Initialized. Using SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        else:
            print(f"INFO: Flask App Initialized. Using SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")

class DevelopmentConfig(Config):
    DEBUG = True
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

# --- Updated ProductionConfig ---
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

    # Ensure psycopg2 compatibility
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql+psycopg2://', 1)

    # Ensure DATABASE_URL is set
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("CRITICAL_ERROR: DATABASE_URL environment variable is NOT SET for production!")

    print(f"INFO [ProductionConfig]: Using production database.")

config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    prod=ProductionConfig,
    default=DevelopmentConfig
)

# --- Fernet Cipher Initialization ---
_fernet_cipher = None
_env_encryption_key = os.getenv('ENCRYPTION_KEY')  # Get key from env

if os.getenv('FLASK_CONFIG') == 'test' and os.getenv('TEST_ENCRYPTION_KEY'):
    _env_encryption_key = os.getenv('TEST_ENCRYPTION_KEY')

if _env_encryption_key:
    try:
        from cryptography.fernet import Fernet
        _fernet_cipher = Fernet(_env_encryption_key.encode())
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
