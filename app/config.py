import os
from dotenv import load_dotenv

# --- Path Setup for .env (primarily for local development) ---
current_script_path = os.path.abspath(__file__)
app_dir = os.path.dirname(current_script_path)
backend_root_dir = os.path.dirname(app_dir) # This is your 'backend' folder
dotenv_path = os.path.join(backend_root_dir, '.env')

# Load .env only if it exists (it won't exist in production on Render unless you create it)
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"DEBUG [config.py]: Successfully loaded .env file from: {dotenv_path}")
else:
    print(f"DEBUG [config.py]: .env file NOT FOUND at: {dotenv_path}. Relying on environment variables set by the platform.")
    # No need for fallback load_dotenv() here if we expect platform to set vars.

# --- Debug Print for DB_URL directly after potential .env loading ---
DB_URL_FROM_ENV = os.getenv('DB_URL') # This will be None in production if not set by platform
print(f"DEBUG [config.py]: Value of os.getenv('DB_URL') after load_dotenv() is: {DB_URL_FROM_ENV}")

DB_HOST_FROM_ENV = os.getenv('DB_HOST') # This will be None in production if not set
print(f"DEBUG [config.py]: Value of os.getenv('DB_HOST') is: {DB_HOST_FROM_ENV}")


class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-very-secure-default-dev-secret-key-please-change-me-for-prod')
    
    # For local dev, this will pick up DB_URL from .env (e.g., sqlite:///dev_app.db)
    # For production, this will be overridden by ProductionConfig
    SQLALCHEMY_DATABASE_URI = DB_URL_FROM_ENV or \
                                'sqlite:///' + os.path.join(backend_root_dir, 'default_app_sqlite.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    RESEND_API_KEY = os.getenv('RESEND_API_KEY')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
    AFRICASTALKING_USERNAME = os.getenv('AFRICASTALKING_USERNAME')
    AFRICASTALKING_API_KEY = os.getenv('AFRICASTALKING_API_KEY')
    FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')
    FIREBASE_AUTH_DOMAIN = os.getenv('FIREBASE_AUTH_DOMAIN')
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')

    @staticmethod
    def init_app(app):
        # Using app.logger which is available after app is created
        if not Config.SECRET_KEY or Config.SECRET_KEY == 'a-very-secure-default-dev-secret-key-please-change-me-for-prod':
            if app and hasattr(app, 'logger'):
                app.logger.warning("WARNING: SECRET_KEY is not set or is using a weak default. Please set a strong SECRET_KEY for production.")
            else:
                print("WARNING: SECRET_KEY is not set or is using a weak default. Please set a strong SECRET_KEY for production.")
        
        # This check is more relevant for local development feedback
        if app and hasattr(app, 'logger') and app.debug: # Only log this verbosely in debug mode
            loaded_db_url = os.getenv('DB_URL')
            if not loaded_db_url:
                app.logger.warning(f"WARNING: DB_URL not found in environment. Using fallback URI: {Config.SQLALCHEMY_DATABASE_URI}")
            elif 'default_app_sqlite.db' in Config.SQLALCHEMY_DATABASE_URI and loaded_db_url != Config.SQLALCHEMY_DATABASE_URI:
                app.logger.warning(f"WARNING: DB_URL was set to '{loaded_db_url}' but resulted in SQLite fallback. Check DB_URL format.")
            elif 'sqlite:///' in Config.SQLALCHEMY_DATABASE_URI:
                app.logger.info(f"INFO: Using SQLite database URI: {Config.SQLALCHEMY_DATABASE_URI}")

        if not Config.ENCRYPTION_KEY:
            if app and hasattr(app, 'logger'):
                app.logger.warning("WARNING: ENCRYPTION_KEY not set. Fingerprint data encryption will be insecure or may fail.")
            else:
                print("WARNING: ENCRYPTION_KEY not set. Fingerprint data encryption will be insecure or may fail.")


class DevelopmentConfig(Config):
    DEBUG = True
    # SQLALCHEMY_ECHO = True 

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DB_URL') or \
                                'sqlite:///' + os.path.join(backend_root_dir, 'test_app.db') # SQLite in backend root for tests
    WTF_CSRF_ENABLED = False 
    SECRET_KEY = os.getenv('TEST_SECRET_KEY', 'test-secret-key')
    ENCRYPTION_KEY = os.getenv('TEST_ENCRYPTION_KEY', Config.ENCRYPTION_KEY or 'test_default_encryption_key_32b_placeholder')


class ProductionConfig(Config):
    DEBUG = False
    # Simplified SQLALCHEMY_DATABASE_URI for Render
    # os.getenv('DATABASE_URL') is the primary source (e.g., for Render's PostgreSQL).
    # 'sqlite:///render_prod_app.db' is the fallback, creating the file in the app root on Render's ephemeral disk.
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'sqlite:///render_prod_app.db'
    print(f"DEBUG [ProductionConfig]: SQLALCHEMY_DATABASE_URI has been set to: {SQLALCHEMY_DATABASE_URI}")

    # Ensure critical environment variables are set in production
    # Changed from raise ValueError to print for less disruptive startup during troubleshooting.
    if not os.getenv('SECRET_KEY') or \
       (hasattr(Config, 'SECRET_KEY') and Config.SECRET_KEY == 'a-very-secure-default-dev-secret-key-please-change-me-for-prod') or \
       os.getenv('SECRET_KEY') == 'a-very-secure-default-dev-secret-key-please-change-me-for-prod': # Check both direct os.getenv and inherited Config.SECRET_KEY if it was set by default
        print("CRITICAL_WARNING [ProductionConfig]: Production SECRET_KEY is not set or is using the default development key. Please set a strong SECRET_KEY for production.")
    
    if not os.getenv('ENCRYPTION_KEY'):
        print("CRITICAL_WARNING [ProductionConfig]: Production ENCRYPTION_KEY is not set. Fingerprint data encryption will be insecure or may fail.")
    
    # Consider adding similar critical warnings for other keys if they are essential for production functionality:
    # if not os.getenv('RESEND_API_KEY'):
    #     print("CRITICAL_WARNING [ProductionConfig]: Production RESEND_API_KEY is not set.")
    # if not os.getenv('AFRICASTALKING_API_KEY'): # and other relevant keys
    #     print("CRITICAL_WARNING [ProductionConfig]: Production AFRICASTALKING_API_KEY is not set.")
    # etc.

# This is the dictionary your app/__init__.py needs to import
config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    prod=ProductionConfig,
    default=DevelopmentConfig 
)

# --- Fernet Cipher Initialization ---
_fernet_cipher = None
# Determine current config for ENCRYPTION_KEY (important for when this module is imported)
# This is a bit tricky as the app isn't created yet. Best to rely on os.getenv directly here.
_env_encryption_key = os.getenv('ENCRYPTION_KEY')
if not _env_encryption_key and (os.getenv('FLASK_CONFIG') == 'test'): # For testing, use the test key if main one isn't set
    _env_encryption_key = os.getenv('TEST_ENCRYPTION_KEY', 'test_default_encryption_key_32b_placeholder')


if _env_encryption_key:
    try:
        from cryptography.fernet import Fernet
        _fernet_cipher = Fernet(_env_encryption_key.encode())
        print("DEBUG [config.py]: Fernet cipher initialized successfully (using direct env var).")
    except ImportError:
        print("WARNING [config.py]: 'cryptography' library not installed. Fingerprint data encryption will not work.")
        _fernet_cipher = None
    except Exception as e:
        print(f"WARNING [config.py]: Invalid ENCRYPTION_KEY format or other Fernet error. Could not initialize Fernet cipher. Error: {e}")
        _fernet_cipher = None 
else:
    print("DEBUG [config.py]: ENCRYPTION_KEY not found in environment, Fernet cipher not initialized.")

def get_fernet_cipher():
    global _fernet_cipher 
    return _fernet_cipher