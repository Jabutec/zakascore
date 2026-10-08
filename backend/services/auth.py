"""Verify Neon Auth access tokens (JWTs).

Neon Auth issues the tokens. This backend only VERIFIES them, using the public keys
published at <NEON_AUTH_URL>/.well-known/jwks.json, so there is no shared secret.

Environment:
    NEON_AUTH_URL        your Neon Auth URL (from the Neon console), e.g.
                         https://ep-xxxx.<region>.aws.neon.tech/<db>/auth
    NEON_AUTH_ISSUER     optional; defaults to the origin of NEON_AUTH_URL
    NEON_AUTH_AUDIENCE   optional; if set, the token's `aud` must match it
"""
import logging
import os
import threading
from urllib.parse import urlparse

import jwt
from dotenv import load_dotenv
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError

load_dotenv()

logger = logging.getLogger(__name__)

NEON_AUTH_URL = os.environ.get("NEON_AUTH_URL", "").strip().rstrip("/")
NEON_AUTH_ISSUER = os.environ.get("NEON_AUTH_ISSUER", "").strip() or None
NEON_AUTH_AUDIENCE = os.environ.get("NEON_AUTH_AUDIENCE", "").strip() or None

# Asymmetric algorithms only. HS256 and "none" are never accepted, so a forged token
# can't be made to verify by signing it with a public key as if it were a secret.
ALLOWED_ALGORITHMS = ["EdDSA", "ES256", "RS256"]
CLOCK_SKEW_SECONDS = 10

_jwks_client: PyJWKClient | None = None
_jwks_lock = threading.Lock()


def _issuer() -> str:
    """The issuer is the origin of the Neon Auth URL (scheme + host, no path)."""
    if NEON_AUTH_ISSUER:
        return NEON_AUTH_ISSUER
    parsed = urlparse(NEON_AUTH_URL)
    return f"{parsed.scheme}://{parsed.netloc}"


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        with _jwks_lock:
            if _jwks_client is None:
                if not NEON_AUTH_URL:
                    raise RuntimeError("NEON_AUTH_URL is not configured")
                # Keys are cached for an hour. PyJWT refetches once when a token
                # names a key id it doesn't have, which covers key rotation.
                _jwks_client = PyJWKClient(
                    f"{NEON_AUTH_URL}/.well-known/jwks.json",
                    cache_jwk_set=True,
                    lifespan=3600,
                    timeout=5,
                )
    return _jwks_client


def verify_access_token(token: str) -> str | None:
    """Return the Neon Auth user id (the token's `sub`) for a valid token, else None.

    Fails closed: a bad signature, wrong issuer, expired token or unreachable key
    endpoint all return None. A missing NEON_AUTH_URL raises RuntimeError, so a
    misconfigured server doesn't look like "everyone is logged out".
    """
    if not token or not isinstance(token, str):
        return None

    client = _get_jwks_client()

    options = {"require": ["exp", "sub"]}
    if NEON_AUTH_AUDIENCE is None:
        options["verify_aud"] = False  # signature + issuer already tie it to your Neon Auth

    try:
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=ALLOWED_ALGORITHMS,
            issuer=_issuer(),
            audience=NEON_AUTH_AUDIENCE,
            leeway=CLOCK_SKEW_SECONDS,
            options=options,
        )
    except PyJWKClientConnectionError:
        logger.error("Could not reach the Neon Auth JWKS endpoint")
        return None
    except jwt.PyJWTError as error:
        logger.warning("Neon Auth token verification failed: %s", type(error).__name__)
        return None

    subject = payload.get("sub")
    return subject if isinstance(subject, str) and subject else None


if __name__ == "__main__":
    # Debug helper:  python -m services.auth <token>
    # Shows what a real Neon Auth token looks like (algorithm, issuer, claims) and
    # whether it verifies. Don't paste real tokens anywhere public.
    import json
    import sys

    raw = sys.argv[1] if len(sys.argv) > 1 else ""
    if not raw:
        raise SystemExit("usage: python -m services.auth <token>")
    print("header:", jwt.get_unverified_header(raw))
    print("claims:", json.dumps(jwt.decode(raw, options={"verify_signature": False}), indent=2))
    print("verified user id:", verify_access_token(raw))