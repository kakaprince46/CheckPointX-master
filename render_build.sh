#!/usr/bin/env bash
# Exit on any error
set -o errexit

echo "INFO [render_build.sh]: Starting build process..."

echo "INFO [render_build.sh]: Upgrading pip..."
python -m pip install --upgrade pip

echo "INFO [render_build.sh]: Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Set FLASK_APP and FLASK_CONFIG for the migration command.
# This ensures that when `flask db upgrade` runs, it loads the
# Flask app using the 'prod' configuration (ProductionConfig).
export FLASK_APP="app:create_app" 
export FLASK_CONFIG="prod" 

echo "INFO [render_build.sh]: FLASK_APP is ${FLASK_APP}"
echo "INFO [render_build.sh]: FLASK_CONFIG is ${FLASK_CONFIG}"

# Optional: Create an instance folder if your SQLite path in ProductionConfig
# is defined as 'sqlite:///instance/your_database_name.db'.
# If your ProductionConfig.SQLALCHEMY_DATABASE_URI is just 'sqlite:///your_database_name.db',
# the database file will be created in the application root on Render, and this mkdir is not strictly needed for the DB.
# However, an 'instance' folder is a common Flask pattern for other instance-specific files.
# if [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" == *"instance/"* ]]; then # Example condition if using instance folder
#     echo "INFO [render_build.sh]: Ensuring instance folder exists for SQLite..."
#     mkdir -p instance 
# fi
# For the current setup where ProductionConfig uses 'sqlite:///render_prod_app.db' (in root of app),
# the mkdir -p instance line is not essential for the database file itself.

echo "INFO [render_build.sh]: Running database migrations (flask db upgrade)..."
flask db upgrade  # This applies migrations using the SQLALCHEMY_DATABASE_URI from ProductionConfig
echo "INFO [render_build.sh]: Database migrations complete."
echo "INFO [render_build.sh]: Build process finished."