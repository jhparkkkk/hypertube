import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_register_user_success():
    """ Test successful user registration """
    client = APIClient()
    payload = {
        "email": "testuser@example.com",
        "username": "testuser",
        "first_name": "John",
        "last_name": "Doe",
        "password": "Test@1234"
    }
    response = client.post("/api/auth/signup", payload, format="json")

    assert response.status_code == 201

    user = User.objects.get(email="testuser@example.com")
    assert user.username == "testuser"
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.auth_provider == "email"

    assert user.password != "Test@1234"
    assert user.check_password("Test@1234")


@pytest.mark.django_db
def test_register_user_invalid_email():
    """ Test registration fails with an invalid email """
    client = APIClient()
    payload = {
        "email": "not-an-email",
        "username": "testuser",
        "first_name": "John",
        "last_name": "Doe",
        "password": "Test@1234"
    }
    response = client.post("/api/auth/signup", payload, format="json")

    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_register_user_missing_fields():
    """ Test registration fails when required fields are missing """
    client = APIClient()
    payload = {
        "email": "testuser@example.com",
        "password": "Test@1234"
    }
    response = client.post("/api/auth/signup", payload, format="json")

    assert response.status_code == 400
    assert "username" in response.data
    assert "first_name" in response.data
    assert "last_name" in response.data


@pytest.mark.django_db
def test_register_user_duplicate_email():
    """ Test registration fails if email is already taken """
    User.objects.create_user(
        email="testuser@example.com",
        username="existinguser",
        first_name="John",
        last_name="Doe",
        password="Test@1234"
    )

    client = APIClient()
    payload = {
        "email": "testuser@example.com",
        "username": "newuser",
        "first_name": "Jane",
        "last_name": "Doe",
        "password": "Test@5678"
    }
    response = client.post("/api/auth/signup", payload, format="json")

    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_register_user_duplicate_username():
    """ Test registration fails if username is already taken """
    User.objects.create_user(
        email="existing@example.com",
        username="testuser",
        first_name="John",
        last_name="Doe",
        password="Test@1234"
    )

    client = APIClient()
    payload = {
        "email": "newuser@example.com",
        "username": "testuser",
        "first_name": "Jane",
        "last_name": "Doe",
        "password": "Test@5678"
    }
    response = client.post("/api/auth/signup", payload, format="json")

    assert response.status_code == 400
    assert "username" in response.data


@pytest.mark.django_db
def test_register_user_weak_password():
    """ Test registration fails when password is too weak """
    client = APIClient()
    payload = {
        "email": "testuser@example.com",
        "username": "testuser",
        "first_name": "John",
        "last_name": "Doe",
        "password": "12345"
    }
    response = client.post("/api/auth/signup", payload, format="json")
    
    assert response.status_code == 400
    assert "password" in response.data


@pytest.mark.django_db
def test_register_user_long_password():
    """ Test registration fails when password is too long """
    client = APIClient()
    payload = {
        "email": "testuser@example.com",
        "username": "testuser",
        "first_name": "John",
        "last_name": "Doe",
        "password": "A" * 51  # Password too long
    }
    response = client.post("/api/auth/signup", payload, format="json")
    
    assert response.status_code == 400
    assert "password" in response.data


@pytest.mark.django_db
def test_register_user_missing_digit_in_password():
    """ Test registration fails when password has no digits """
    client = APIClient()
    payload = {
        "email": "testuser@example.com",
        "username": "testuser",
        "first_name": "John",
        "last_name": "Doe",
        "password": "OnlyLetters"
    }
    response = client.post("/api/auth/signup", payload, format="json")
    
    assert response.status_code == 400
    assert "password" in response.data


@pytest.mark.django_db
def test_register_user_missing_letter_in_password():
    """ Test registration fails when password has no letters """
    client = APIClient()
    payload = {
        "email": "testuser@example.com",
        "username": "testuser",
        "first_name": "John",
        "last_name": "Doe",
        "password": "12345678"
    }
    response = client.post("/api/auth/signup", payload, format="json")
    
    assert response.status_code == 400
    assert "password" in response.data


@pytest.mark.django_db
def test_register_user_different_providers():
    """ Test that a user cannot register with different providers """
    User.objects.create_user(
        email="testuser@example.com",
        username="testuser",
        first_name="John",
        last_name="Doe",
        password="Test@1234",
        auth_provider="github"
    )

    client = APIClient()
    payload = {
        "email": "testuser@example.com",
        "username": "testuser2",
        "first_name": "Jane",
        "last_name": "Doe",
        "password": "Test@5678",
        "auth_provider": "fortytwo"
    }
    response = client.post("/api/auth/signup", payload, format="json")

    assert response.status_code == 400
    assert "email" in response.data
