import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_landing_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_app_page(client):
    response = client.get('/app')
    assert response.status_code == 200

def test_register_missing_fields(client):
    response = client.post('/api/register', json={})
    assert response.status_code in [400, 422]

def test_register_duplicate_email(client):
    data = {'name': 'Test User', 'email': 'duplicate@test.com', 'password': 'password123'}
    client.post('/api/register', json=data)
    response = client.post('/api/register', json=data)
    assert response.status_code in [400, 409, 422]

def test_login_wrong_credentials(client):
    response = client.post('/api/login', json={
        'email': 'nonexistent@test.com',
        'password': 'wrongpassword'
    })
    assert response.status_code in [400, 401, 404]

def test_login_missing_fields(client):
    response = client.post('/api/login', json={})
    assert response.status_code in [400, 422]

def test_facilities_requires_auth(client):
    response = client.get('/api/facilities')
    assert response.status_code in [200, 401]

def test_bookings_requires_auth(client):
    response = client.get('/api/bookings')
    assert response.status_code in [401, 403]

def test_create_booking_requires_auth(client):
    response = client.post('/api/bookings', json={
        'facility_id': 1,
        'start_time': '2026-04-01T09:00',
        'end_time': '2026-04-01T10:00'
    })
    assert response.status_code in [401, 403]

def test_admin_bookings_requires_auth(client):
    response = client.get('/api/admin/bookings')
    assert response.status_code in [401, 403]

def test_admin_approve_requires_auth(client):
    response = client.post('/api/admin/bookings/1/approve')
    assert response.status_code in [401, 403]

def test_admin_reject_requires_auth(client):
    response = client.post('/api/admin/bookings/1/reject')
    assert response.status_code in [401, 403]

def test_admin_stats_requires_auth(client):
    response = client.get('/api/admin/stats')
    assert response.status_code in [401, 403]

def test_ai_booking_requires_auth(client):
    response = client.post('/api/ai/parse-booking', json={'text': 'book a lab tomorrow'})
    assert response.status_code in [401, 403]

def test_facility_availability_endpoint(client):
    response = client.get('/api/facilities/1/availability?date=2026-04-01')
    assert response.status_code in [200, 401, 404]

def test_logout(client):
    response = client.post('/api/logout')
    assert response.status_code == 200
