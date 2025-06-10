import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# --- Path Setup for .env (primarily for local development, but harmless in prod) ---
# This part is still useful if you ever want to test production settings locally with a .env file.
current_script_path = os.path.abspath(__file__)
app_dir = os.path.dirname(current_script_path)
backend_root_dir = os.path.dirname(app_dir)
dotenv_path = os.path.join(backend_root_dir, '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

class Config:
    """Base configuration class."""
    # Load all settings from environment variables.
    # Production environments like Render should provide these.
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    RESEND_API_KEY = os.getenv('RESEND_API_KEY')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
    AFRICASTALKING_USERNAME = os.getenv('AFRICASTALKING_USERNAME')
    AFRICASTALKING_API_KEY = os.getenv('AFRICASTALKING_API_KEY')
    FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')
    FIREBASE_AUTH_DOMAIN = os.getenv('FIREBASE_AUTH_DOMAIN')
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')

    # Default SQLALCHEMY_DATABASE_URI will be overridden by ProductionConfig
    SQLALCHEMY_DATABASE_URI = None

    @staticmethod
    def init_app(app):
        # You can add logging for initialized services here if needed
        pass

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    # Production ALWAYS uses the DATABASE_URL from the environment (set by Render for its PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

    # This is a critical check. If DATABASE_URL is not set on Render, the app will fail to start.
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("CRITICAL_ERROR: No DATABASE_URL set for production environment!")
    
    # Render's default PostgreSQL URL starts with 'postgres://'.
    # SQLAlchemy and psycopg2 work better with 'postgresql://' or 'postgresql+psycopg2://'.
    # This code replaces it to ensure compatibility.
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # This print statement is crucial for debugging your Render deployment.
    # It will show in the logs which database your app is trying to connect to.
    print(f"INFO [ProductionConfig]: Using production database URI: {SQLALCHEMY_DATABASE_URI}")

    # Ensure other critical environment variables are set
    if not os.getenv('SECRET_KEY'):
        raise ValueError("CRITICAL_ERROR: Production SECRET_KEY is not set!")
    if not os.getenv('ENCRYPTION_KEY'):
        raise ValueError("CRITICAL_WARNING: Production ENCRYPTION_KEY is not set!")

# The dictionary now only points to ProductionConfig.
# The `create_app` function in your app/__init__.py will need to be adjusted
# to not expect 'dev' or 'test', or to default to 'prod'.
config_by_name = dict(
    prod=ProductionConfig,
    default=ProductionConfig  # Default to production config
)

# --- Fernet Cipher Initialization ---
_fernet_cipher = None
_env_encryption_key = os.getenv('ENCRYPTION_KEY')

if _env_encryption_key:
    try:
        _fernet_cipher = Fernet(_env_encryption_key.encode())
        print("DEBUG [config.py]: Fernet cipher initialized successfully.")
    except ImportError:
        print("WARNING [config.py]: 'cryptography' library not installed. Encryption will not work.")
        _fernet_cipher = None
    except Exception as e:
        print(f"WARNING [config.gpy]: Invalid ENCRYPTION_KEY format. Fernet cipher failed. Error: {e}")
        _fernet_cipher = None
else:
    print("DEBUG [config.py]: ENCRYPTION_KEY not found, Fernet cipher not initialized.")

def get_fernet_cipher():
    """Returns the globally initialized Fernet cipher instance."""
    global _fernet_cipher
    return _fernet_cipher