from app import app, db

with app.app_context():
    try:
        # Try connecting to the database and running a simple query
        db.session.execute('SELECT 1')
        print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {e}")


