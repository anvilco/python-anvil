"""Builds the Authorization header, the same way node-anvil does."""

from __future__ import annotations

import base64
import binascii
import json
import re
from typing import Any


# Three dot-separated base64url segments. The signature can be empty.
JWT_RE = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*$")


def build_auth_header(
    api_key: str | None = None, access_token: str | None = None
) -> str:
    """The Authorization header for an API key or an OAuth access token.

    An API key is sent with HTTP Basic auth, as `base64(api_key + ":")`.
    Anvil's OAuth access tokens are JWTs, which the API wants as-is:
    `Bearer <access_token>`. Any other kind of token is base64 encoded, which
    the API still accepts for backwards compatibility.

    If both are given, the access token is used.
    """
    if access_token:
        if is_jwt(access_token):
            return f"Bearer {access_token}"
        return f"Bearer {_base64(access_token)}"
    if api_key:
        return f"Basic {_base64(f'{api_key}:')}"
    raise ValueError("`api_key` or `access_token` is required")


def is_jwt(token: Any) -> bool:
    """Whether a token is a JWT: three base64url segments where the header and payload decode to JSON objects.

    This is a bit stricter than the API's check, so anything it says yes to,
    the API will treat as a JWT too.
    """
    if not isinstance(token, str) or not JWT_RE.match(token):
        return False

    header, payload = (_decode_json_segment(s) for s in token.split(".")[:2])
    return bool(header and payload and isinstance(header.get("alg"), str))


def _decode_json_segment(segment: str) -> dict[str, Any] | None:
    try:
        padded = segment + "=" * (-len(segment) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(padded))
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return None
    return decoded if isinstance(decoded, dict) else None


def _base64(value: str) -> str:
    return base64.b64encode(value.encode("ascii")).decode("ascii")
