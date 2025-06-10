#!/usr/bin/env bash
# Exit on any error
set -o errexit

echo "INFO [render_build.sh]: Starting build process..."
pip install --upgrade pip
pip install -r requirements.txt

# Set FLASK_APP and FLASK_CONFIG for the migration command
export FLASK_APP="app:create_app"
export FLASK_CONFIG="prod"

echo "INFO [render_build.sh]: FLASK_CONFIG is ${FLASK_CONFIG}"
echo "INFO [render_build.sh]: About to run database migrations (flask db upgrade)..."

# This command applies migrations to the database specified in ProductionConfig,
# which is pulled from the DATABASE_URL environment variable.
flask db upgrade

echo "INFO [render_build.sh]: Database migrations complete."
echo "INFO [render_build.sh]: Build process finished."