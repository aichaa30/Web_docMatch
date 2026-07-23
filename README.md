# DocMatch

A full-stack web application that helps patients find doctors near them who accept their insurance, built collaboratively by a 4-person team during our Software Engineering course sequence at Syracuse University.

## Demo

[Watch the demo video(coming soon)](your-video-link-here)

<img width="2866" height="1536" alt="image" src="https://github.com/user-attachments/assets/0f3beeeb-a955-43fd-adb8-c68bb3bd05dc" />


## About

DocMatch lets users create an account, search for doctors by specialty and location, and save favorites for later. The goal was to simplify the process of finding in-network healthcare providers and reduce friction around insurance-related appointment issues.

## Features

- Secure user registration with email confirmation
- Login/logout with hashed password authentication
- Password reset via email
- Doctor search by specialty and location
- Favorite doctors for quick access later
- Editable user profile

## Tech Stack

**Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Migrate (Alembic), Flask-Login, Flask-Bcrypt, Flask-Mail

**Database:** PostgreSQL

**Frontend:** HTML, CSS, Bootstrap, JavaScript

**Deployment:** Render, Gunicorn

**Process:** Agile/Scrum, Jira, Git/GitHub

## Team

- Kayla Cedeño
- Raychel Hernandez-Jones
- Aicha Gory (Team Lead)
- Kyle Laylor

## My Role

As team lead, I ran sprint planning and tracked our work in Jira, and wrote our sprint reports. On the technical side, I designed the PostgreSQL database schema, built the backend authentication system (registration, login, email verification, password reset), implemented the doctor search and favorites features, and handled deployment to Render.

## Technical Deep Dive

### Database Schema
Built with PostgreSQL, using Flask-SQLAlchemy to define the data models in Python instead of writing raw SQL. Schema changes (like adding new columns) are tracked with Alembic/Flask-Migrate, so they can be applied consistently anywhere the app runs. Main tables:
- **user**: account info (name, email, hashed password, insurance details, address)
- **Doctor**: provider records imported from the NPI Registry API (name, specialty, phone, address)
- **favorites**: links users to the doctors they've saved

### Authentication
- Passwords are never stored as plain text. Flask-Bcrypt scrambles (hashes) them before saving, and compares hashes at login instead of comparing raw passwords
- Flask-Login keeps track of who is logged in during a session
- Email confirmation and password reset links use itsdangerous to generate secure tokens that expire after one hour, so links can't be reused or guessed

### Deployment
- Hosted on Render, running through Gunicorn (a production-ready server, since Flask's built-in server is only meant for local testing)
- Database is a managed PostgreSQL instance, also on Render
- All secrets (like the database URL and email password) are stored as environment variables, not written directly in the code, and loaded automatically when the app starts
- Database changes are applied using `flask db upgrade` to keep the schema consistent

## Screenshots

<img width="2870" height="1398" alt="image" src="https://github.com/user-attachments/assets/8cc644a5-fd04-4670-ace5-3e51b2cc6c2a" />
<img width="2706" height="1506" alt="image" src="https://github.com/user-attachments/assets/2f910f3a-357c-4cc8-81ba-00ff7ccadaf1" />
<img width="2838" height="986" alt="image" src="https://github.com/user-attachments/assets/1d6e86f7-a27d-48de-a1dc-a3eae755b88d" />




## Running Locally

1. Clone the repo
2. Create a virtual environment and install dependencies: `pip install -r requirements.txt`
3. Set up a `.env` file with `SECRET_KEY`, `DATABASE_URL`, `MAIL_USERNAME`, `MAIL_PASSWORD`
4. Run migrations: `flask db upgrade`
5. Start the app: `python app.py`

## Known Limitations

- Doctor specialty search is currently limited to a fixed list of specialties from the imported dataset
- Hosted on a free-tier database that may require periodic recreation
