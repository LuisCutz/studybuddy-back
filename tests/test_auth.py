import unittest

from app.core.security import create_access_token, decode_access_token, get_password_hash, verify_password


class AuthSecurityTests(unittest.TestCase):
    def test_password_hashing_and_verification(self):
        raw_password = "secret123"
        hashed_password = get_password_hash(raw_password)

        self.assertTrue(verify_password(raw_password, hashed_password))
        self.assertFalse(verify_password("wrong-password", hashed_password))

    def test_access_token_contains_user_and_tenant_claims(self):
        token = create_access_token(user_id="user-123", tenant_id="tenant-1")
        payload = decode_access_token(token)

        self.assertEqual(payload["sub"], "user-123")
        self.assertEqual(payload["tenant_id"], "tenant-1")


if __name__ == "__main__":
    unittest.main()
