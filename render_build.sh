#!/usr/bin/env bash
# Exit on any error
set -o errexit

echo "INFO [render_build.sh]: Starting build process..."

echo "INFO [render_build.sh]: Upgrading pip..."
python -m pip install --upgrade pip

echo "INFO [render_build.sh]: Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Set FLASK_APP and FLASK_CONFIG for the migration command
export FLASK_APP="app:create_app" 
export FLASK_CONFIG="prod" # This ensures ProductionConfig is used by flask CLI

echo "INFO [render_build.sh]: FLASK_APP set to ${FLASK_APP}"
echo "INFO [render_build.sh]: FLASK_CONFIG set to ${FLASK_CONFIG}"

# Optional: Create an instance folder if your SQLite path used it (e.g., instance/render_prod_app.db)
# If SQLALCHEMY_DATABASE_URI = 'sqlite:///render_prod_app.db' (in root), this is not strictly needed for the DB file itself.
# However, Flask instance folders are good practice for other instance-specific files.
# echo "INFO [render_build.sh]: Ensuring instance folder exists (if used by app)..."
# mkdir -p instance 

echo "INFO [render_build.sh]: About to run database migrations (flask db upgrade)..."
flask db upgrade  # This applies migrations using the SQLALCHEMY_DATABASE_URI from ProductionConfig
echo "INFO [render_build.sh]: Database migrations complete."
echo "INFO [render_build.sh]: Build process finished."