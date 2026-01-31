from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import hashlib
import bcrypt

load_dotenv()


class Security:
    @staticmethod
    def hash_password(plain_password):
    # Convert the password to bytes
        pw_bytes = plain_password.encode('utf-8')
        # Generate salt with cost factor 12
        salt = bcrypt.gensalt(rounds=12)
        # Hash the password
        hashed = bcrypt.hashpw(pw_bytes, salt)
        return hashed
    @staticmethod
    def verify_password(plain_password, hashed_password):
    # Convert the password to bytes
        pw_bytes = plain_password.encode('utf-8')
        # Verify the password
        return bcrypt.checkpw(pw_bytes, hashed_password)
#✅ JWT payload must be a dict
class JWT:
    @staticmethod
    def create_access_token(payload):
        return jwt.encode(payload, "secret", algorithm="HS256")

    @staticmethod
    def decode_token(token):
        return jwt.decode(token, "secret", algorithms=["HS256"])