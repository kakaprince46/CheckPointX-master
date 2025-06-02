#!/usr/bin/env bash
# Exit on any error
set -o errexit

echo "INFO [render_build.sh]: Starting build process..."

echo "INFO [render_build.sh]: Upgrading pip..."
python -m pip install --upgrade pip # More explicit way to call pip from current python

echo "INFO [render_build.sh]: Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Set FLASK_APP and FLASK_CONFIG for the migration command
# These will be used by Flask CLI to load the correct app instance and configuration.
export FLASK_APP="app:create_app" 
export FLASK_CONFIG="prod" # Ensure ProductionConfig is used for migrations

echo "INFO [render_build.sh]: FLASK_APP set to ${FLASK_APP}"
echo "INFO [render_build.sh]: FLASK_CONFIG set to ${FLASK_CONFIG}"
echo "INFO [render_build.sh]: About to run database migrations (flask db upgrade)..."

flask db upgrade

echo "INFO [render_build.sh]: Database migrations complete."
echo "INFO [render_build.sh]: Build process finished."