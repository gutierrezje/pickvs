from datetime import timedelta

import jwt

from utils.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_returns_different_hashes():
    password = "SecurePassword123!"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    assert hash1 != hash2
    assert hash1.startswith("$2b$")  # bcrypt hash prefix
    assert hash2.startswith("$2b$")


def test_verify_password():
    password = "AnotherSecurePassword!"
    hashed = hash_password(password)
    assert verify_password(password, hashed)


def test_verify_wrong_password():
    password = "Password1!"
    wrong_password = "Password2!"
    hashed = hash_password(password)
    assert verify_password(wrong_password, hashed) is False


def test_create_access_token_contains_payload():
    user_id = "user123"
    data = {"sub": user_id}
    token = create_access_token(data)
    payload = jwt.decode(token, options={"verify_signature": False})
    assert payload["sub"] == user_id
    assert "exp" in payload


def test_decode_access_token_valid():
    user_id = "user456"
    data = {"sub": user_id}
    token = create_access_token(data)
    payload = decode_access_token(token)
    assert payload["sub"] == user_id
    assert "exp" in payload


def test_decode_access_token_expired():
    user_id = "user789"
    data = {"sub": user_id}
    # Create a token that expires immediately
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))
    try:
        decode_access_token(token)
        raise AssertionError("Expected ValueError for expired token")
    except ValueError as e:
        assert str(e) == "Token has expired"
