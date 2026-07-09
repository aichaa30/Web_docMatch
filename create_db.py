from app import app, db  # Import app and db

# Ensure you're working within the app context
with app.app_context():
    db.create_all()  # Create all tables defined in models.py
    print("Tables created successfully!")
