import sqlite3
import os

# Get the directory where this script itself is located (should be 'backend')
script_dir = os.path.dirname(__file__) 

# Construct the path to the database file inside the 'instance' subfolder
db_path = os.path.join(script_dir, 'instance', 'dev_app.db')

print(f"Attempting to connect to SQLite database at: {db_path}")

if not os.path.exists(db_path):
    print(f"ERROR: Database file not found at {db_path}")
    print("Please ensure that `flask db upgrade` has run successfully and that the database file exists in the 'instance' folder within your backend directory.")
else:
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("\n--- Users Table Contents ---")
        # Execute a query to select all data from the users table
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()

        if rows:
            # Get column names
            column_names = [description[0] for description in cursor.description]
            print(column_names)
            for row in rows:
                print(row)
        else:
            print("No data found in the users table. (This is normal if you haven't registered any users yet from your frontend).")

        # You can also check other tables, e.g., registrations:
        # print("\n--- Registrations Table Contents ---")
        # cursor.execute("SELECT * FROM registrations")
        # reg_rows = cursor.fetchall()
        # if reg_rows:
        #     reg_column_names = [description[0] for description in cursor.description]
        #     print(reg_column_names)
        #     for reg_row in reg_rows:
        #         print(reg_row)
        # else:
        #     print("No data found in the registrations table.")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        # Close the connection
        if conn:
            conn.close()
            print("\nDatabase connection closed.")