from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import hashlib
import bcrypt

load_dotenv()

# JWT configuration from environment
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "60"))


class Security:
    @staticmethod
    def hash_password(plain_password):
        """Hash a plain-text password and return a UTF-8 string for DB storage."""
        pw_bytes = plain_password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(pw_bytes, salt)
        # Store as text, not bytes
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password, hashed_password):
        """Verify a plain-text password against a stored hash string."""
        pw_bytes = plain_password.encode("utf-8")
        # Ensure stored hash is bytes for bcrypt.checkpw
        hashed_bytes = (
            hashed_password.encode("utf-8")
            if isinstance(hashed_password, str)
            else hashed_password
        )
        return bcrypt.checkpw(pw_bytes, hashed_bytes)


class JWT:
    """JWT helper using environment-based secret and expiry."""

    @staticmethod
    def create_access_token(payload):
        """Create a signed access token.

        The payload *must* be a dict. `exp` and `iat` claims are added automatically
        based on JWT_EXP_MINUTES.
        """
        if not isinstance(payload, dict):
            raise ValueError("JWT payload must be a dict")

        to_encode = payload.copy()
        now = datetime.utcnow()
        expire_delta_minutes = JWT_EXP_MINUTES or 60
        to_encode.update(
            {
                "iat": now,
                "exp": now + timedelta(minutes=expire_delta_minutes),
            }
        )

        return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def verify_token(token):
        """Verify a token and return the decoded payload or None if invalid/expired."""
        try:
            return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except JWTError:
            return None


