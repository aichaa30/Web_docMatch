import pytest
from app import app, db
from models.models import User
from unittest.mock import patch


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


def test_register_success(client):
    with patch('app.mail.send') as mock_send, \
            patch('app.serializer.dumps', return_value='fake-token'), \
            patch('flask.url_for', return_value='http://localhost/confirm/fake-token'):

        response = client.post('/register', data={
            'full_name': 'Test User',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm': 'password123',
            'insurance_details': 'XYZ Insurance',
            'city': 'Syracuse',
            'zip_code': '13244',
            'address': '123 University Place'
        }, follow_redirects=True)

        assert b'Account created! Check your email to confirm your account.' in response.data
        assert User.query.filter_by(email='test@example.com').first() is not None
        mock_send.assert_called_once()


def test_register_invalid_email(client):
    response = client.post('/register', data={
        'full_name': 'Test User',
        'email': 'invalidemail',
        'password': 'password123',
        'confirm': 'password123',
        'insurance_details': 'XYZ Insurance',
        'city': 'Syracuse',
        'zip_code': '13244',
        'address': '123 University Place'
    }, follow_redirects=True)

    assert b'Invalid email format.' in response.data


def test_register_password_mismatch(client):
    response = client.post('/register', data={
        'full_name': 'Test User',
        'email': 'test2@example.com',
        'password': 'password123',
        'confirm': 'wrongpassword',
        'insurance_details': 'XYZ Insurance',
        'city': 'Syracuse',
        'zip_code': '13244',
        'address': '123 University Place'
    }, follow_redirects=True)

    assert b'Passwords do not match.' in response.data


def test_register_existing_email(client):
    user = User(
        full_name='Existing User',
        email='test3@example.com',
        password='password123',
        insurance_details='XYZ Insurance',
        city='Syracuse',
        zip_code='13244',
        address='123 University Place'
    )
    db.session.add(user)
    db.session.commit()

    response = client.post('/register', data={
        'full_name': 'New User',
        'email': 'test3@example.com',
        'password': 'password123',
        'confirm': 'password123',
        'insurance_details': 'New Insurance',
        'city': 'Buffalo',
        'zip_code': '10001',
        'address': '456 Elm Street'
    }, follow_redirects=True)

    assert b'Email already registered. Please log in.' in response.data


def test_register_missing_email(client):
    response = client.post('/register', data={
        'full_name': 'Test User',
        'email': '',
        'password': 'password123',
        'confirm': 'password123',
        'insurance_details': 'XYZ Insurance',
        'city': 'Syracuse',
        'zip_code': '13244',
        'address': '123 University Place'
    }, follow_redirects=True)

    assert b'Invalid email format.' in response.data


def test_register_empty_fields(client):
    response = client.post('/register', data={}, follow_redirects=True)
    assert b'Invalid email format.' in response.data or b'Passwords do not match.' in response.data


def test_register_short_password(client):
    response = client.post('/register', data={
        'full_name': 'Test User',
        'email': 'shortpass@example.com',
        'password': 'short',
        'confirm': 'short',
        'insurance_details': 'XYZ Insurance',
        'city': 'Syracuse',
        'zip_code': '13244',
        'address': '123 University Place'
    }, follow_redirects=True)



    assert b'Account created! Check your email to confirm your account.' in response.data


def test_register_long_fields(client):
    long_string = 'a' * 300  # Assuming max length is less than 300
    response = client.post('/register', data={
        'full_name': long_string,
        'email': 'longfield@example.com',
        'password': 'password123',
        'confirm': 'password123',
        'insurance_details': long_string,
        'city': long_string,
        'zip_code': '13244',
        'address': long_string
    }, follow_redirects=True)

    # If DB enforces limits, this would throw an error.
    # adjust based on model constraints.
    assert b'Account created! Check your email to confirm your account.' in response.data


def test_register_special_chars_email(client):
    response = client.post('/register', data={
        'full_name': 'Test User',
        'email': "test!#$%&'*+-/=?^_`{|}~@example.com",
        'password': 'password123',
        'confirm': 'password123',
        'insurance_details': 'XYZ Insurance',
        'city': 'Syracuse',
        'zip_code': '13244',
        'address': '123 University Place'
    }, follow_redirects=True)

    assert b'Account created! Check your email to confirm your account.' in response.data


def test_register_duplicate_submission(client):
    user_data = {
        'full_name': 'Duplicate User',
        'email': 'duplicate@example.com',
        'password': 'password123',
        'confirm': 'password123',
        'insurance_details': 'XYZ Insurance',
        'city': 'Syracuse',
        'zip_code': '13244',
        'address': '123 University Place'
    }
    client.post('/register', data=user_data, follow_redirects=True)

    response = client.post('/register', data=user_data, follow_redirects=True)
    assert b'Email already registered. Please log in.' in response.data


def test_register_invalid_zip(client):
    response = client.post('/register', data={
        'full_name': 'Test User',
        'email': 'invalidzip@example.com',
        'password': 'password123',
        'confirm': 'password123',
        'insurance_details': 'XYZ Insurance',
        'city': 'Syracuse',
        'zip_code': 'abcde',
        'address': '123 University Place'
    }, follow_redirects=True)

    # route doesn’t validate zip codes yet, so this still passes
    assert b'Account created! Check your email to confirm your account.' in response.data


def test_register_boundary_cases(client):
    max_length_name = 100
    min_length_password = 8

    valid_name = 'a' * max_length_name
    valid_password = 'p' * min_length_password

    with patch('app.mail.send') as mock_send, \
            patch('app.serializer.dumps', return_value='fake-token'), \
            patch('flask.url_for', return_value='http://localhost/confirm/fake-token'):

        response = client.post('/register', data={
            'full_name': valid_name,
            'email': 'boundary@example.com',
            'password': valid_password,
            'confirm': valid_password,
            'insurance_details': 'Boundary Insurance',
            'city': 'Boundary City',
            'zip_code': '13244',
            'address': 'Boundary Address'
        }, follow_redirects=True)

        assert b'Account created! Check your email to confirm your account.' in response.data
        assert User.query.filter_by(email='boundary@example.com').first() is not None
        mock_send.assert_called_once()
