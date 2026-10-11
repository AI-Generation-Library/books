import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

ISSUER = "knowledge-hub-local"
AUDIENCE = "knowledge-hub-api"


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return base64.b64encode(salt + digest).decode()


def verify_password(password: str, stored: str) -> bool:
    value = base64.b64decode(stored)
    actual = hashlib.scrypt(password.encode(), salt=value[:16], n=16384, r=8, p=1)
    return hmac.compare_digest(actual, value[16:])


def issue_token(user_id: int, secret: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user_id), "iss": ISSUER, "aud": AUDIENCE,
                       "iat": now, "nbf": now, "exp": now + timedelta(minutes=15)},
                      secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> dict:
    return jwt.decode(token, secret, algorithms=["HS256"], issuer=ISSUER,
                      audience=AUDIENCE,
                      options={"require": ["sub", "iss", "aud", "exp", "nbf", "iat"]})
