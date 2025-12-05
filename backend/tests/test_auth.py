
def test_register_success(db_connection, client):
    """Test successful user registration."""
    response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "user_id" in data
    assert data["message"] == "User registered successfully"


def test_register_existing_username(db_connection, client):
    """Test registration with existing username."""
    user_data = {
        "username": "user123",
        "email": "user@example.com",
        "password": "SecurePass123!",
    }

    # First registration should succeed
    response1 = client.post("/auth/register", json=user_data)
    assert response1.status_code == 201

    # Change email but keep username the same
    user_data["email"] = "duplicate@example.com"
    response2 = client.post("/auth/register", json=user_data)
    assert response2.status_code == 409
    assert response2.json()["detail"] == "Username already exists"

def test_register_existing_email(db_connection, client):
    """Test registration with existing email."""
    user_data = {
        "username": "uniqueuser",
        "email": "user@example.com",
        "password": "SecurePass123!",
    }
    # First registration should succeed
    response1 = client.post("/auth/register", json=user_data)
    assert response1.status_code == 201
    # Change username but keep email the same
    user_data["username"] = "dupeuser"
    response2 = client.post("/auth/register", json=user_data)
    assert response2.status_code == 409
    assert response2.json()["detail"] == "Email already registered"

def test_login_success(db_connection, client):
    """Test successful user login."""
    user_data = {
        "username": "loginuser",
        "email": "login@example.com",
        "password": "SecurePass123!",
    }

    # Register user first
    reg_response = client.post("/auth/register", json=user_data)
    assert reg_response.status_code == 201
    # Attempt login
    login_response = client.post(
        "/auth/login",
        json={
            "username": user_data["username"],
            "password": user_data["password"],
        },
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(db_connection, client):
    """Test login with invalid credentials."""
    user_data = {
        "username": "validuser",
        "email": "valid@example.com",
        "password": "SecurePass123!",
    }
    # Register user first
    reg_response = client.post("/auth/register", json=user_data)
    assert reg_response.status_code == 201
    # Attempt login with wrong password
    login_response = client.post(
        "/auth/login",
        json={
            "username": user_data["username"],
            "password": "WrongPassword!",
        },
    )
    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Invalid username or password"
    # Attempt login with non-existent username
    login_response2 = client.post(
        "/auth/login",
        json={
            "username": "nonuser",
            "password": "StrongPass123!",
        },
    )
    assert login_response2.status_code == 401
    assert login_response2.json()["detail"] == "Invalid username or password"