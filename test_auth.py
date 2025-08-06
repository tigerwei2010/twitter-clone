import pytest
import os
from datetime import UTC, datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt, JWTError

# Import the functions we want to test
from auth import create_access_token, verify_token, get_current_user, SECRET_KEY, ALGORITHM


class TestCreateAccessToken:
    """Test the create_access_token function"""

    def test_create_access_token_basic(self):
        """Test basic token creation"""
        data = {"user_id": 123456789, "email": "test@example.com"}
        token = create_access_token(data)

        # Token should be a string
        assert isinstance(token, str)

        # Should have 3 parts separated by dots (JWT format)
        parts = token.split('.')
        assert len(parts) == 3

        # Decode and verify the payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["user_id"] == 123456789
        assert payload["email"] == "test@example.com"
        assert "exp" in payload

    def test_create_access_token_with_custom_expiry(self):
        """Test token creation with custom expiration time"""
        data = {"user_id": 123456789, "email": "test@example.com"}
        expires_delta = timedelta(minutes=30)

        token = create_access_token(data, expires_delta)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[
                             ALGORITHM], options={"verify_sub": False})

        # Check that expiration is approximately 30 minutes from now
        exp_time = datetime.fromtimestamp(payload["exp"], UTC)
        expected_exp = datetime.now(UTC) + expires_delta

        # Allow 5 second tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 5

    def test_create_access_token_default_expiry(self):
        """Test that default expiry is 6 months"""
        data = {"user_id": 123456789, "email": "test@example.com"}
        token = create_access_token(data)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"], UTC)

        # Should expire approximately 6 months from now (180 days)
        expected_exp = datetime.now(UTC) + timedelta(days=180)

        # Allow 1 day tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 86400

    def test_create_access_token_empty_data(self):
        """Test token creation with empty data"""
        data = {}
        token = create_access_token(data)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload  # Should still have expiration

    def test_create_access_token_additional_claims(self):
        """Test token creation with additional claims"""
        data = {
            "user_id": 123456789,
            "email": "test@example.com",
            "role": "admin",
            "permissions": ["read", "write"]
        }
        token = create_access_token(data)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["user_id"] == 123456789
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]


class TestVerifyToken:
    """Test the verify_token function"""

    def test_verify_token_valid(self):
        """Test verification of a valid token"""
        # Create a valid token
        data = {"user_id": 123456789, "email": "test@example.com"}
        token = create_access_token(data)

        # Mock HTTPAuthorizationCredentials
        credentials = MagicMock()
        credentials.credentials = token

        # Verify the token
        result = verify_token(credentials)

        assert result["user_id"] == 123456789
        assert result["email"] == "test@example.com"

    def test_verify_token_expired(self):
        """Test verification of an expired token"""
        # Create an expired token
        data = {"user_id": 123456789, "email": "test@example.com"}
        expired_time = datetime.now(UTC) - timedelta(minutes=1)

        # Manually create expired token
        payload = data.copy()
        payload["exp"] = expired_time
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        credentials = MagicMock()
        credentials.credentials = expired_token

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_token(credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in str(
            exc_info.value.detail)

    def test_verify_token_invalid_signature(self):
        """Test verification of token with invalid signature"""
        # Create token with wrong secret
        data = {"user_id": 123456789, "email": "test@example.com"}
        wrong_token = jwt.encode(data, "wrong-secret", algorithm=ALGORITHM)

        credentials = MagicMock()
        credentials.credentials = wrong_token

        with pytest.raises(HTTPException) as exc_info:
            verify_token(credentials)

        assert exc_info.value.status_code == 401

    def test_verify_token_malformed(self):
        """Test verification of malformed token"""
        credentials = MagicMock()
        credentials.credentials = "invalid.token.format"

        with pytest.raises(HTTPException) as exc_info:
            verify_token(credentials)

        assert exc_info.value.status_code == 401

    def test_verify_token_missing_sub(self):
        """Test verification of token missing required 'sub' claim"""
        # Create token without 'sub' claim
        data = {"email": "test@example.com"}
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

        credentials = MagicMock()
        credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            verify_token(credentials)

        assert exc_info.value.status_code == 401

    def test_verify_token_missing_email(self):
        """Test verification of token missing required 'email' claim"""
        # Create token without 'email' claim
        data = {"user_id": 123456789}
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

        credentials = MagicMock()
        credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            verify_token(credentials)

        assert exc_info.value.status_code == 401

    def test_verify_token_none_values(self):
        """Test verification of token with None values"""
        # Create token with None values
        data = {"user_id": None, "email": "test@example.com"}
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

        credentials = MagicMock()
        credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            verify_token(credentials)

        assert exc_info.value.status_code == 401


class TestGetCurrentUser:
    """Test the get_current_user function"""

    def test_get_current_user_valid_token(self):
        """Test get_current_user with valid token data"""
        token_data = {"user_id": 123456789, "email": "test@example.com"}

        result = get_current_user(token_data)

        assert result == token_data

    def test_get_current_user_integration(self):
        """Test get_current_user integration with verify_token"""
        # This would typically be tested with FastAPI's dependency injection
        # For now, we just test that the function passes through the token data
        token_data = {
            "user_id": 987654321,
            "email": "integration@example.com"
        }

        result = get_current_user(token_data)

        assert result["user_id"] == 987654321
        assert result["email"] == "integration@example.com"


class TestAuthConfiguration:
    """Test authentication configuration"""

    def test_secret_key_from_environment(self):
        """Test that SECRET_KEY uses environment variable when available"""
        with patch.dict(os.environ, {'JWT_SECRET_KEY': 'test-secret-from-env'}):
            # Reimport to pick up the new environment variable
            import importlib
            import auth
            importlib.reload(auth)

            assert auth.SECRET_KEY == 'test-secret-from-env'

    def test_secret_key_default(self):
        """Test that SECRET_KEY uses default when environment variable not set"""
        with patch.dict(os.environ, {}, clear=True):
            # Remove JWT_SECRET_KEY if it exists
            if 'JWT_SECRET_KEY' in os.environ:
                del os.environ['JWT_SECRET_KEY']

            import importlib
            import auth
            importlib.reload(auth)

            assert auth.SECRET_KEY == 'your-secret-key-change-in-production'

    def test_algorithm_configuration(self):
        """Test that algorithm is set correctly"""
        from auth import ALGORITHM
        assert ALGORITHM == "HS256"

    def test_token_expire_months_configuration(self):
        """Test that token expiration is set to 6 months"""
        from auth import ACCESS_TOKEN_EXPIRE_MONTHS
        assert ACCESS_TOKEN_EXPIRE_MONTHS == 6


class TestTokenLifecycle:
    """Test complete token lifecycle"""

    def test_create_and_verify_token_cycle(self):
        """Test creating a token and then verifying it"""
        # Step 1: Create token
        user_data = {"user_id": 555666777, "email": "lifecycle@example.com"}
        token = create_access_token(user_data)

        # Step 2: Verify token
        credentials = MagicMock()
        credentials.credentials = token

        verified_data = verify_token(credentials)

        # Step 3: Check data matches
        assert verified_data["user_id"] == user_data["user_id"]
        assert verified_data["email"] == user_data["email"]

    def test_token_with_different_user_ids(self):
        """Test tokens for different users are unique"""
        user1_data = {"user_id": 111111111, "email": "user1@example.com"}
        user2_data = {"user_id": 222222222, "email": "user2@example.com"}

        token1 = create_access_token(user1_data)
        token2 = create_access_token(user2_data)

        # Tokens should be different
        assert token1 != token2

        # Verify each token returns correct user data
        creds1 = MagicMock()
        creds1.credentials = token1
        verified1 = verify_token(creds1)

        creds2 = MagicMock()
        creds2.credentials = token2
        verified2 = verify_token(creds2)

        assert verified1["user_id"] == 111111111
        assert verified2["user_id"] == 222222222
        assert verified1["email"] == "user1@example.com"
        assert verified2["email"] == "user2@example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
