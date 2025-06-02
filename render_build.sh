#!/usr/bin/env bash
# Exit on any error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Set FLASK_APP and FLASK_ENV for the migration command
# Render will use FLASK_CONFIG for the running app if you set it in env vars
export FLASK_APP="app:create_app" 
# For migrations, it's often fine to run them with a 'production' like config,
# but ensure your ProductionConfig in config.py correctly loads DATABASE_URL
# from Render's environment variables.
export FLASK_ENV="production" # Or use FLASK_CONFIG=prod if your config.py uses that

echo "INFO: Running database migrations..."
flask db upgrade
echo "INFO: Database migrations complete."

# Note: Gunicorn (your web server) will be started by Render's "Start Command"
# This script is only for the build phase.