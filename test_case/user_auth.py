import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import random
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import os
from fastapi.staticfiles import StaticFiles

from main import app  # now this will work


client = TestClient(app)



if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# Common valid data for a new user
def generate_valid_user():
    return {
        "user_name": f"TestUser{random.randint(1000, 9999)}",
        "user_email": f"test{random.randint(1000, 9999)}@example.com",
        "phone": "+919876543210",
        "user_password": "ValidPass123!",
        "confirm_password": "ValidPass123!",
        "user_type": "user",
        "status": "active"
    }

def test_register_valid_user():
    user = generate_valid_user()
    # Simulate OTP already verified
    # This depends on your DB, so you might need to mock this step
    response = client.post("/auth/v1/register", json=user)
    assert response.status_code == 200
    assert "Registration successful" in response.json()["message"]

# Test Case 2: Email already registered
def test_register_email_already_registered():
    user = generate_valid_user()
    # First registration
    client.post("/auth/v1/register", json=user)
    # Second registration with same email
    response = client.post("/auth/v1/register", json=user)
    assert response.status_code == 400
    assert response.json()["detail"] in [
        "Email already registered",
        "Please verify your email before registration."
    ]

# Test Case 3: Invalid email format
def test_register_invalid_email_format():
    user = generate_valid_user()
    user["user_email"] = "invalid-email"
    response = client.post("/auth/v1/register", json=user)
    assert response.status_code == 400
    assert "Invalid email format" in response.json()["detail"]

# Test Case 4: Weak password
def test_register_weak_password():
    user = generate_valid_user()
    user["user_password"] = "weak"
    user["confirm_password"] = "weak"
    response = client.post("/auth/v1/register", json=user)
    assert response.status_code == 400
    assert "Password must" in response.json()["detail"]

# Test Case 5: Password mismatch
def test_register_password_mismatch():
    user = generate_valid_user()
    user["confirm_password"] = "NotMatching123!"
    response = client.post("/auth/v1/register", json=user)
    assert response.status_code == 400
    assert response.json()["detail"] == "Passwords do not match"
