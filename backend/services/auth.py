import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import jwt


load_dotenv()


JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


def create_access_token(user_id: str, merchant_id: str | None = None) -> str:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not configured")

    payload = {
        "user_id": user_id,
        "exp": datetime.now() + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_access_token(token: str) -> str | None:
    if not JWT_SECRET:
        return None

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("user_id") or payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
