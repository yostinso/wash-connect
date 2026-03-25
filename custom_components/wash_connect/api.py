"""Async API client for the Wash Connect laundry service."""
from __future__ import annotations

import aiohttp

# ---------------------------------------------------------------------------
# Base URLs and shared constants
# ---------------------------------------------------------------------------

_FIREBASE_BASE = "https://us-central1-washmobilepay.cloudfunctions.net"

# Hardcoded in the app binary — not a user secret.
_WEB_API_KEY = "gc8g4so8c0swo4cock0gckgkck844gg0skk8ooc0"

_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class WashConnectError(Exception):
    """Base exception for all Wash Connect API errors."""


class AuthError(WashConnectError):
    """Raised on authentication failures (bad credentials, expired/missing token)."""


class ApiError(WashConnectError):
    """Raised on non-auth API errors (bad srcode, unexpected response, etc.)."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _base_headers() -> dict[str, str]:
    """Headers required on every Firebase Functions request."""
    return {"provider": "kiosoft"}


def _auth_headers(token: str) -> dict[str, str]:
    return {**_base_headers(), "Authorization": f"Bearer {token}"}


def _require_token(token: str | None) -> str:
    if not token:
        raise AuthError("No session token — call login() first")
    return token


async def _parse_response(resp: aiohttp.ClientResponse) -> dict:
    """
    Decode a JSON response and raise the appropriate exception on failure.

    HTTP 401/403 → AuthError
    Any other non-2xx or a JSON body with status != 200 → ApiError
    """
    if resp.status in (401, 403):
        raise AuthError(f"HTTP {resp.status}")

    if resp.status >= 400:
        raise ApiError(f"HTTP {resp.status}")

    body = await resp.json(content_type=None)

    status = body.get("status")
    if status == 401:
        raise AuthError(body.get("message", "Unauthorized"))
    if status is not None and status != 200 and status != "ok":
        raise ApiError(f"API error status={status}: {body.get('message', body)}")

    return body


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class WashConnectClient:
    """Async client for the Wash Connect API."""

    def __init__(
        self,
        token: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._token = token
        self._session = session

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    async def login(self, email: str, password: str) -> dict:
        """
        Authenticate with email + password.

        Tries plaintext first (isEncrypted=false).  Returns the raw login
        response dict and caches the token internally.
        The server returns HTTP 400 for bad credentials, which is re-raised
        as AuthError.

        isEncrypted: true is not currently implemented since that would require
        discovering the client-side encryption method and replicating it here.
        """
        if not email or not password:
            raise AuthError("Email and password are required")

        payload = {"login": email, "password": password, "isEncrypted": False}
        try:
            body = await self._post_firebase("/login", payload, auth=False)
        except ApiError as exc:
            raise AuthError(str(exc)) from exc

        self._token = body["token"]
        return body

    # ------------------------------------------------------------------
    # Locations
    # ------------------------------------------------------------------

    async def get_locations(self, srcode: str) -> dict:
        """Look up location metadata for a site code.  Returns the location dict.

        Notably this is a public endpoint that does not require authentication.
        """
        body = await self._get_firebase("/locations", params={"srcode": srcode}, auth=False)
        location = body.get("location")
        if not location:
            raise ApiError(f"No location found for srcode={srcode!r}")
        return location

    # ------------------------------------------------------------------
    # Machine status
    # ------------------------------------------------------------------

    async def get_machine_status(self, uln: str) -> dict:
        """
        Fetch machine status for a location.
        Returns a dict keyed by floor index:

        Notably this is a public endpoint that does not require authentication.
          { "1": { "name": "1st Floor", "machines": [...] }, ... }
        """
        body = await self._get_firebase(
            "/get_machine_status_v1",
            params={"uln": uln},
            auth=False,
        )
        return body["data"]

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------

    async def get_account_balance(self) -> int:
        """Return the account balance in cents as an integer."""
        token = _require_token(self._token)
        body = await self._get_firebase("/account_balance", token=token)
        return int(body["account_balance"])

    # ------------------------------------------------------------------
    # Token renewal
    # ------------------------------------------------------------------

    async def get_user_token(self, user_id: str, uuid: str) -> str:
        """
        Obtain a user_token for the secondary (www.getwashconnect.com) API.

        This is a separate credential from the login Bearer token.
        """
        token = _require_token(self._token)
        body = await self._post_firebase(
            "/get_token",
            {"user_id": user_id, "uuid": uuid},
            token=token,
        )
        return body["user_token"]

    # ------------------------------------------------------------------
    # Low-level request helpers
    # ------------------------------------------------------------------

    def _get_session(self) -> aiohttp.ClientSession:
        """Return the shared session, creating a temporary one if none was injected."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _get_firebase(
        self,
        path: str,
        *,
        params: dict | None = None,
        token: str | None = None,
        auth: bool = True,
    ) -> dict:
        headers = _auth_headers(token) if (auth and token) else _base_headers()
        url = f"{_FIREBASE_BASE}{path}"
        async with self._get_session().get(
            url, headers=headers, params=params, timeout=_REQUEST_TIMEOUT
        ) as resp:
            return await _parse_response(resp)

    async def _post_firebase(
        self,
        path: str,
        payload: dict,
        *,
        token: str | None = None,
        auth: bool = True,
    ) -> dict:
        headers = _auth_headers(token) if (auth and token) else _base_headers()
        url = f"{_FIREBASE_BASE}{path}"
        async with self._get_session().post(
            url, headers=headers, json=payload, timeout=_REQUEST_TIMEOUT
        ) as resp:
            return await _parse_response(resp)
