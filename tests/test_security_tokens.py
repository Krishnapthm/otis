import os
import unittest

os.environ.setdefault(
    "DB_URL", "postgresql+asyncpg://user:password@localhost:5432/otis"
)
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
)

from src.core import security


class SecurityTokenTests(unittest.TestCase):
    def setUp(self):
        security._refresh_token_store.clear()

    def test_access_and_refresh_token_types(self):
        access_token = security.create_access_token({"sub": "user@example.com"})
        refresh_token = security.create_refresh_token({"sub": "user@example.com"})

        access_payload = security.decode_token(access_token, expected_type="access")
        refresh_payload = security.decode_token(refresh_token, expected_type="refresh")

        self.assertEqual(access_payload["sub"], "user@example.com")
        self.assertEqual(access_payload["typ"], "access")
        self.assertEqual(refresh_payload["typ"], "refresh")

    def test_refresh_jti_store_validate_and_revoke(self):
        subject = "user@example.com"
        jti = "test-jti"

        security.store_refresh_jti(subject, jti)
        self.assertTrue(security.validate_refresh_jti(subject, jti))

        security.revoke_refresh_jti(subject)
        self.assertFalse(security.validate_refresh_jti(subject, jti))


if __name__ == "__main__":
    unittest.main()
