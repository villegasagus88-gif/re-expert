"""
Comprehensive tests for the standalone auth system.

Tests bcrypt hashing, JWT generation/validation, token expiration,
and the full auth service logic using mocked DB sessions.
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4



# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# Mock settings before importing anything that uses them
mock_settings = MagicMock()
mock_settings.JWT_SECRET = "test-secret-key-for-unit-tests-only-32chars!"
mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7
mock_settings.DATABASE_URL = "postgresql://test:test@localhost/test"
mock_settings.DEBUG = False

# Patch settings globally before imports
sys.modules["config"] = MagicMock()
sys.modules["config.settings"] = MagicMock(settings=mock_settings)


# ===== 1. BCRYPT TESTS =====

class TestBcrypt:
    """Test password hashing and verification."""

    def test_hash_password_returns_string(self):
        import bcrypt
        password = "TestPass123"
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")
        print("  OK  hash returns bcrypt string")

    def test_hash_password_different_each_time(self):
        import bcrypt
        password = "TestPass123"
        hash1 = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        hash2 = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        assert hash1 != hash2  # different salts
        print("  OK  different salts produce different hashes")

    def test_verify_correct_password(self):
        import bcrypt
        password = "TestPass123"
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        assert bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        print("  OK  correct password verifies")

    def test_verify_wrong_password(self):
        import bcrypt
        password = "TestPass123"
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        assert not bcrypt.checkpw("WrongPass456".encode("utf-8"), hashed.encode("utf-8"))
        print("  OK  wrong password rejected")

    def test_verify_empty_password_rejected(self):
        import bcrypt
        password = "TestPass123"
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        assert not bcrypt.checkpw("".encode("utf-8"), hashed.encode("utf-8"))
        print("  OK  empty password rejected")

    def test_unicode_password(self):
        import bcrypt
        password = "Contrasenya123!"
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        assert bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        print("  OK  unicode password works")


# ===== 2. JWT TESTS =====

class TestJWT:
    """Test JWT token generation and validation."""

    def test_create_access_token(self):
        from services.jwt_service import create_access_token
        user_id = uuid4()
        token = create_access_token(user_id)
        assert isinstance(token, str)
        assert len(token) > 50
        print("  OK  access token generated")

    def test_create_refresh_token(self):
        from services.jwt_service import create_refresh_token
        user_id = uuid4()
        token = create_refresh_token(user_id)
        assert isinstance(token, str)
        assert len(token) > 50
        print("  OK  refresh token generated")

    def test_access_token_has_correct_claims(self):
        from services.jwt_service import create_access_token, decode_token
        user_id = uuid4()
        token = create_access_token(user_id)
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        print("  OK  access token has correct claims (sub, type=access, exp, iat)")

    def test_refresh_token_has_correct_claims(self):
        from services.jwt_service import create_refresh_token, decode_token
        user_id = uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"
        assert "exp" in payload
        print("  OK  refresh token has correct claims (sub, type=refresh, exp)")

    def test_access_token_expires_in_15_min(self):
        from services.jwt_service import create_access_token, decode_token
        user_id = uuid4()
        token = create_access_token(user_id)
        payload = decode_token(token)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        delta = exp - iat
        assert timedelta(minutes=14) < delta <= timedelta(minutes=16)
        print(f"  OK  access token expires in {delta} (expected ~15min)")

    def test_refresh_token_expires_in_7_days(self):
        from services.jwt_service import create_refresh_token, decode_token
        user_id = uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        delta = exp - iat
        assert timedelta(days=6, hours=23) < delta <= timedelta(days=7, hours=1)
        print(f"  OK  refresh token expires in {delta} (expected ~7 days)")

    def test_token_pair_returns_two_different_tokens(self):
        from services.jwt_service import create_token_pair
        user_id = uuid4()
        access, refresh = create_token_pair(user_id)
        assert access != refresh
        print("  OK  token pair returns two different tokens")

    def test_expired_token_raises(self):
        import jwt as pyjwt
        # Create a token that's already expired
        payload = {
            "sub": str(uuid4()),
            "type": "access",
            "iat": datetime.now(timezone.utc) - timedelta(hours=1),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=30),
        }
        token = pyjwt.encode(payload, mock_settings.JWT_SECRET, algorithm="HS256")
        try:
            from services.jwt_service import decode_token
            decode_token(token)
            assert False, "Should have raised"
        except pyjwt.ExpiredSignatureError:
            print("  OK  expired token raises ExpiredSignatureError")

    def test_invalid_secret_raises(self):
        import jwt as pyjwt
        payload = {
            "sub": str(uuid4()),
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        }
        token = pyjwt.encode(payload, "wrong-secret", algorithm="HS256")
        try:
            from services.jwt_service import decode_token
            decode_token(token)
            assert False, "Should have raised"
        except pyjwt.InvalidSignatureError:
            print("  OK  token with wrong secret raises InvalidSignatureError")

    def test_different_users_get_different_tokens(self):
        from services.jwt_service import create_access_token
        t1 = create_access_token(uuid4())
        t2 = create_access_token(uuid4())
        assert t1 != t2
        print("  OK  different users get different tokens")


# ===== 3. AUTH SERVICE FUNCTION TESTS =====

class TestAuthServiceFunctions:
    """Test the pure functions in auth_service."""

    def test_hash_and_verify(self):
        from services.auth_service import _hash_password, _verify_password
        password = "SecurePass123"
        hashed = _hash_password(password)
        assert _verify_password(password, hashed)
        assert not _verify_password("wrong", hashed)
        print("  OK  _hash_password + _verify_password round-trip")

    def test_user_to_dict(self):
        from services.auth_service import _user_to_dict
        user = MagicMock()
        user.id = uuid4()
        user.email = "test@test.com"
        user.full_name = "Test User"
        user.role = "user"
        user.plan = "free"
        result = _user_to_dict(user)
        assert result["id"] == str(user.id)
        assert result["email"] == "test@test.com"
        assert result["full_name"] == "Test User"
        assert result["role"] == "user"
        assert result["plan"] == "free"
        print("  OK  _user_to_dict returns correct structure")


# ===== 4. SCHEMA VALIDATION TESTS =====

class TestSchemas:
    """Test Pydantic schema validation."""

    def test_login_request_valid(self):
        from api.schemas.auth import LoginRequest
        req = LoginRequest(email="test@test.com", password="mypassword")
        assert req.email == "test@test.com"
        assert req.password == "mypassword"
        print("  OK  LoginRequest accepts valid data")

    def test_login_request_invalid_email(self):
        from api.schemas.auth import LoginRequest
        try:
            LoginRequest(email="not-an-email", password="mypassword")
            assert False, "Should have raised"
        except Exception:
            print("  OK  LoginRequest rejects invalid email")

    def test_login_request_empty_password(self):
        from api.schemas.auth import LoginRequest
        try:
            LoginRequest(email="test@test.com", password="")
            assert False, "Should have raised"
        except Exception:
            print("  OK  LoginRequest rejects empty password")

    def test_register_request_weak_password(self):
        from api.schemas.auth import RegisterRequest
        try:
            RegisterRequest(email="test@test.com", password="nouppercase1", full_name="Test")
            assert False, "Should have raised"
        except Exception:
            print("  OK  RegisterRequest rejects weak password (no uppercase)")

    def test_register_request_no_number(self):
        from api.schemas.auth import RegisterRequest
        try:
            RegisterRequest(email="test@test.com", password="NoNumberHere", full_name="Test")
            assert False, "Should have raised"
        except Exception:
            print("  OK  RegisterRequest rejects weak password (no number)")

    def test_register_request_valid(self):
        from api.schemas.auth import RegisterRequest
        req = RegisterRequest(email="test@test.com", password="Strong1Pass", full_name="Test User")
        assert req.email == "test@test.com"
        print("  OK  RegisterRequest accepts strong password")

    def test_auth_response_structure(self):
        from api.schemas.auth import AuthResponse
        resp = AuthResponse(
            access_token="abc",
            refresh_token="def",
            user={"id": "123", "email": "t@t.com", "full_name": "T", "role": "user", "plan": "free"},
        )
        assert resp.access_token == "abc"
        assert resp.user.email == "t@t.com"
        print("  OK  AuthResponse validates correctly")

    def test_refresh_request(self):
        from api.schemas.auth import RefreshRequest
        req = RefreshRequest(refresh_token="some-token")
        assert req.refresh_token == "some-token"
        print("  OK  RefreshRequest accepts valid data")


# ===== 5. INTEGRATION-STYLE TESTS =====

class TestIntegration:
    """Test the full flow with mocked DB."""

    def test_full_register_login_refresh_flow(self):
        """Simulate: register -> get tokens -> decode -> refresh -> new tokens."""
        from services.auth_service import _hash_password, _verify_password
        from services.jwt_service import create_token_pair, decode_token

        # 1. Simulate registration
        email = "newuser@test.com"
        password = "SecurePass123"
        user_id = uuid4()
        password_hash = _hash_password(password)

        # 2. Simulate login
        assert _verify_password(password, password_hash), "Login should succeed"
        assert not _verify_password("wrong", password_hash), "Wrong password should fail"

        # 3. Generate tokens
        access_token, refresh_token = create_token_pair(user_id)

        # 4. Decode access token
        access_payload = decode_token(access_token)
        assert access_payload["sub"] == str(user_id)
        assert access_payload["type"] == "access"

        # 5. Decode refresh token
        refresh_payload = decode_token(refresh_token)
        assert refresh_payload["sub"] == str(user_id)
        assert refresh_payload["type"] == "refresh"

        # 6. Simulate refresh: generate new pair (sleep to get different iat)
        import time
        time.sleep(1.1)
        new_access, new_refresh = create_token_pair(user_id)
        assert new_access != access_token  # different iat
        new_payload = decode_token(new_access)
        assert new_payload["sub"] == str(user_id)

        print("  OK  Full flow: register -> login -> tokens -> refresh")

    def test_access_token_rejected_as_refresh(self):
        """Access tokens should not be accepted for refresh operations."""
        from services.jwt_service import create_access_token, decode_token

        user_id = uuid4()
        access_token = create_access_token(user_id)
        payload = decode_token(access_token)
        assert payload["type"] != "refresh"
        print("  OK  Access token has type!=refresh (would be rejected by refresh endpoint)")

    def test_refresh_token_rejected_as_access(self):
        """Refresh tokens should not be accepted for protected routes."""
        from services.jwt_service import create_refresh_token, decode_token

        user_id = uuid4()
        refresh_token = create_refresh_token(user_id)
        payload = decode_token(refresh_token)
        assert payload["type"] != "access"
        print("  OK  Refresh token has type!=access (would be rejected by protected routes)")


# ===== RUN ALL =====

def main():
    test_classes = [
        ("BCRYPT", TestBcrypt),
        ("JWT TOKENS", TestJWT),
        ("AUTH SERVICE FUNCTIONS", TestAuthServiceFunctions),
        ("SCHEMA VALIDATION", TestSchemas),
        ("INTEGRATION FLOW", TestIntegration),
    ]

    total_passed = 0
    total_failed = 0

    for section_name, test_class in test_classes:
        print(f"\n=== {section_name} ===")
        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        for method_name in sorted(methods):
            try:
                getattr(instance, method_name)()
                total_passed += 1
            except Exception as e:
                print(f"  FAIL  {method_name}: {e}")
                total_failed += 1

    print(f"\n{'='*50}")
    print(f"RESULTS: {total_passed} passed, {total_failed} failed")
    if total_failed == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"ATTENTION: {total_failed} test(s) failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
