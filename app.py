from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mail import Mail, Message
import re
from extensions import db, bcrypt
from models.models import User
from flask_migrate import Migrate
from itsdangerous import URLSafeTimedSerializer
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
DATABASE_URL = os.getenv("DATABASE_URL")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Check your .env file or Render environment variables.")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Check your .env file or Render environment variables.")

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

# Secret Key
app.secret_key = SECRET_KEY

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD

mail = Mail(app)

# Token Serializer for Email Confirmation
serializer = URLSafeTimedSerializer(app.secret_key)

# Initialize Database Tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['email'] = user.email
            session['full_name'] = user.full_name
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']
        insurance_details = request.form['insurance_details']
        city = request.form['city']
        zip_code = request.form['zip_code']
        address = request.form['address']

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email format.')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please log in.')
            return redirect(url_for('login'))

        new_user = User(full_name, email, password, insurance_details, city, zip_code, address)
        db.session.add(new_user)
        db.session.commit()

        token = serializer.dumps(email, salt='email-confirm')
        confirm_url = url_for('confirm_email', token=token, _external=True)
        msg = Message('Confirm Your Email', sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f'Hello {full_name},\n\nPlease confirm your email by clicking the link below:\n{confirm_url}\n\nBest,\nDocMatch Team'
        mail.send(msg)

        flash('Account created! Check your email to confirm your account.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
    except Exception:
        flash('The confirmation link is invalid or has expired.')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()
    if user and not user.is_confirmed:
        user.is_confirmed = True
        db.session.commit()
        flash('Your email has been confirmed! You can now log in.')
    else:
        flash('Invalid confirmation request.')

    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'email' in session and 'full_name' in session:
        return render_template('dashboard.html')
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('full_name', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            token = serializer.dumps(email, salt='password-reset')
            reset_url = url_for('reset_password', token=token, _external=True)

            msg = Message('Password Reset Request', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Hello {user.full_name},\n\nTo reset your password, click the link below:\n{reset_url}\n\nBest,\nDocMatch Team'
            mail.send(msg)

            flash('Check your email for the password reset link.')
            return redirect(url_for('login'))
        else:
            flash('Email not found.')

    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset', max_age=3600)
    except Exception:
        flash('The reset link is invalid or has expired.')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid reset request.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match.')
        else:
            user.set_password(new_password)
            db.session.commit()
            flash('Your password has been reset. You can now log in.')
            return redirect(url_for('login'))

    return render_template('reset_password.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'email' not in session:
        flash('You need to log in to access your profile.')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['email']).first()

    if request.method == 'POST':
        full_name = request.form['full_name']
        new_email = request.form['email']
        insurance_details = request.form['insurance_details']
        city = request.form['city']
        zip_code = request.form['zip_code']
        address = request.form['address']

        if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
            flash('Invalid email format.')
            return render_template('profile.html', user=user)

        if new_email != user.email:
            token = serializer.dumps(new_email, salt='email-update')
            confirm_url = url_for('confirm_new_email', token=token, _external=True)

            msg = Message('Confirm Your New Email', sender=app.config['MAIL_USERNAME'], recipients=[new_email])
            msg.body = f"Hello {full_name},\n\nTo confirm your new email address, click the link below:\n{confirm_url}\n\nIf you did not request this change, ignore this email.\n\nBest,\nDocMatch Team"
            mail.send(msg)

            flash('A confirmation email has been sent to your new email. Please verify to update your email.')
            return redirect(url_for('profile'))

        user.full_name = full_name
        user.insurance_details = insurance_details
        user.city = city
        user.zip_code = zip_code
        user.address = address

        try:
            db.session.commit()
            session['full_name'] = full_name
            flash('Profile updated successfully!')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}')

    return render_template('profile.html', user=user)


@app.route('/confirm_new_email/<token>')
def confirm_new_email(token):
    try:
        new_email = serializer.loads(token, salt='email-update', max_age=3600)
    except Exception:
        flash('The email confirmation link is invalid or has expired.')
        return redirect(url_for('profile'))

    user = User.query.filter_by(email=session['email']).first()

    if user:
        user.email = new_email
        db.session.commit()
        session['email'] = new_email
        flash('Your email has been successfully updated!')
    else:
        flash('User not found.')

    return redirect(url_for('profile'))


@app.route('/search_doctors', methods=['GET'])
def search_doctors():
    specialty = request.args.get('specialty', '').strip().lower()
    location = request.args.get('location', '').strip()

    if not specialty and not location:
        flash("Please enter at least one search criterion.")
        return redirect(url_for('dashboard'))

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        available_specialties = [
            "Massage Therapist",
            "Clinic/Center, Dental",
            "Skilled Nursing Facility",
            "Social Worker, Clinical",
            "Dentist, General Practice",
            "Dentist",
            "Speech-Language Pathologist",
            "Non-emergency Medical Transport (VAN)",
            "Psychologist",
            "Home Health",
            "Early Intervention Provider Agency",
            "Durable Medical Equipment & Medical Supplies, Dialysis Equipment & Supplies",
            "Contractor, Home Modifications",
            "Physical Therapist",
            "Obstetrics & Gynecology",
            "Case Management",
            "Social Worker",
            "Specialist"
        ]

        query = '''SELECT authorized_official_first_name, authorized_official_last_name, 
                          telephone_number, description, address_1, city, postal_code 
                   FROM public."Doctor" WHERE 1=1'''
        params = []

        if specialty:
            matching_specialties = [s for s in available_specialties if specialty in s.lower()]
            if not matching_specialties:
                return render_template('dashboard.html', doctors=[], no_results=True)

            query += ' AND ('
            query += ' OR '.join(['LOWER(description) = %s' for _ in matching_specialties])
            query += ')'
            params.extend([s.lower() for s in matching_specialties])

        if location:
            if location.isdigit() and len(location) >= 5:
                zip_code = location[:5]
                closest_zip = find_closest_zip_code(zip_code)
                if 13000 <= int(closest_zip) < 14000:
                    query += ' AND LEFT(postal_code, 5) = %s'
                    params.append(closest_zip)
                else:
                    return render_template('dashboard.html', doctors=[], no_results=True)
            else:
                query += ''' AND (LOWER(city) LIKE %s 
                               OR LOWER(authorized_official_first_name) LIKE %s 
                               OR LOWER(authorized_official_last_name) LIKE %s)'''
                params.extend([f"%{location.lower()}%"] * 3)

        query += ' AND LEFT(postal_code, 5) ~ %s'
        params.append('^13[0-9]{3}$')

        cursor.execute(query, tuple(params))
        doctors = cursor.fetchall()

        doctor_list = []
        for doctor in doctors:
            doctor_list.append({
                "authorized_official_first_name": doctor[0],
                "authorized_official_last_name": doctor[1],
                "telephone_number": doctor[2],
                "description": doctor[3],
                "address_1": doctor[4],
                "city": doctor[5],
                "postal_code": doctor[6]
            })

        cursor.close()
        conn.close()

        return render_template('dashboard.html', doctors=doctor_list, no_results=(len(doctor_list) == 0))

    except Exception as e:
        flash(f"Database error: {str(e)}")
        return redirect(url_for('dashboard'))


def find_closest_zip_code(user_zip):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute('SELECT DISTINCT LEFT(postal_code, 5) FROM public."Doctor";')
        zip_codes = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        if not zip_codes:
            return user_zip

        closest_zip = min(zip_codes, key=lambda z: abs(int(z) - int(user_zip)))
        return closest_zip

    except Exception as e:
        print(f"Error finding closest zip code: {str(e)}")
        return user_zip


@app.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    try:
        data = request.get_json()
        doctor_full_name = data.get('doctor_full_name')
        telephone_number = data.get('telephone_number')
        postal_code = str(data.get('postal_code'))
        action = data.get('action')

        email = session.get('email')
        if not email:
            return jsonify({"success": False, "message": "User not logged in"})

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        if action == 'add':
            cursor.execute('''
                INSERT INTO favorites (email, doctor_full_name, telephone_number, postal_code)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            ''', (email, doctor_full_name, telephone_number, postal_code))

        if action == 'remove':
            delete_query = '''DELETE FROM favorites 
                  WHERE email = %s
                  AND doctor_full_name = %s 
                  AND telephone_number = %s 
                  AND postal_code = %s'''
            cursor.execute(delete_query, (email, doctor_full_name, telephone_number, postal_code))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True})

    except Exception as e:
        print(f"Error encountered: {e}")
        return jsonify({"success": False, "message": str(e)})


@app.route('/favorites')
def show_favorites():
    try:
        email = session.get('email')
        if not email:
            flash("Please log in to view your favorites.")
            return redirect(url_for('login'))

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT d.authorized_official_first_name, d.authorized_official_last_name, 
                   d.telephone_number, d.description, d.address_1, d.city, d.postal_code
            FROM favorites f
            JOIN "Doctor" d 
              ON f.doctor_full_name = d.authorized_official_first_name || ' ' || d.authorized_official_last_name
             AND f.telephone_number = d.telephone_number
             AND f.postal_code = d.postal_code
            WHERE f.email = %s
        ''', (email,))

        doctors = cursor.fetchall()
        cursor.close()
        conn.close()

        doctor_list = [{
            "first_name": doctor[0],
            "last_name": doctor[1],
            "telephone": doctor[2],
            "specialty": doctor[3],
            "address": doctor[4],
            "city": doctor[5],
            "postal_code": doctor[6]
        } for doctor in doctors]

        return render_template('favorites.html', favorites=doctor_list)
    except Exception as e:
        flash(f"Error retrieving favorites: {str(e)}")
        return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=False)