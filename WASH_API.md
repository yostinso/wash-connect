# WASH Connect API

Reverse-engineered from MITM capture of the WASH Connect Android app (March 2026).

## Overview

The app uses two separate backends:

| Backend | Base URL | Purpose |
|---------|----------|---------|
| Firebase Cloud Functions | `https://us-central1-washmobilepay.cloudfunctions.net` | Auth, machine status, account balance |
| Secondary web API | `https://www.getwashconnect.com/api/` | Auto-refill settings, extended account info |

This document covers the Firebase backend, which is sufficient for reading machine status and account balance.

---

## Common Headers

Every request to the Firebase backend requires:

```
provider: kiosoft
```

Authenticated requests also require:

```
Authorization: Bearer <token>
```

The `token` is obtained from `POST /login` and is a long opaque string (CryptoJS-encrypted, base64-ish).

---

## Authentication

### `POST /login`

Authenticate with email and password.

**Request body (JSON):**

```json
{
  "login": "user@example.com",
  "password": "plaintext-password",
  "isEncrypted": false
}
```

> **Note:** The app supports `isEncrypted: true` with CryptoJS AES encryption, but `isEncrypted: false` with plaintext works and is simpler to implement.

**Response (200 OK):**

```json
{
  "token": "U2FsdGVkX1/...",
  "user_id": "595122",
  "last_uln": "CA7527907",
  "account_balance": "1175"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `token` | string | Bearer token for subsequent authenticated requests |
| `user_id` | string | Numeric user ID (as a string) |
| `last_uln` | string | ULN of the last location the user interacted with |
| `account_balance` | string | Current balance in cents, as a string |

**Error responses:**

- `HTTP 400` — Bad credentials (wrong password, unknown email). The API uses 400 rather than 401 here.

---

## Locations

### `GET /locations?srcode=<srcode>`

Look up metadata for a laundry location by site code. **Public — no authentication required.**

**Query parameters:**

| Parameter | Description |
|-----------|-------------|
| `srcode` | Site code printed on signage at the location (e.g. `W001274`) |

**Response (200 OK):**

```json
{
  "location": {
    "uln": "CA7527907",
    "location_name": "The Laundry Room",
    "location_id": "12345"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `uln` | string | Unit Location Number — used in machine status queries. **May contain leading/trailing whitespace; always `.strip()` before use.** |
| `location_name` | string | Human-readable name of the laundry room |
| `location_id` | string | Internal numeric ID |

**Error responses:**

- Response body with `status != 200` / empty `location` — invalid or unknown `srcode`.

---

## Machine Status

### `GET /get_machine_status_v1?uln=<uln>`

Fetch real-time status of all machines at a location. **Public — no authentication required.**

**Query parameters:**

| Parameter | Description |
|-----------|-------------|
| `uln` | Unit Location Number (from `/locations` or login response) |

**Response (200 OK):**

```json
{
  "data": {
    "1": {
      "name": "1st Floor",
      "machines": [
        {
          "machine_number": "001",
          "bt_name": "bt001",
          "last_user": "connect",
          "start_time": "2026-03-23T15:05:08.000Z",
          "status": "available",
          "time_remaining": "0",
          "type": "washer"
        },
        {
          "machine_number": "002",
          "bt_name": "bt002",
          "last_user": "connect",
          "start_time": "2026-03-23T14:20:00.000Z",
          "status": "in_use",
          "time_remaining": "45",
          "type": "dryer"
        }
      ]
    },
    "2": {
      "name": "2nd Floor",
      "machines": [...]
    }
  }
}
```

The top-level response has a `data` key containing a floor map. Floors are keyed by a numeric string (`"1"`, `"2"`, …).

**Floor object:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Human-readable floor name (e.g. `"1st Floor"`) |
| `machines` | array | List of machine objects on this floor |

**Machine object:**

| Field | Type | Description |
|-------|------|-------------|
| `machine_number` | string | Display number (e.g. `"001"`) |
| `bt_name` | string | Bluetooth advertisement name — unique identifier for the machine |
| `type` | string | `"washer"` or `"dryer"` |
| `status` | string | `"available"`, `"in_use"`, or `"out_of_service"` |
| `time_remaining` | string | Minutes remaining as a string; `"0"` when not in use |
| `start_time` | string | ISO 8601 UTC timestamp of the last cycle start (e.g. `"2026-03-23T15:05:08.000Z"`); may be stale if the machine has been idle for a while |
| `last_user` | string | Username of the last user; often `"connect"` for kiosk-started cycles |

> **Known data quirk:** The same `bt_name` can appear on multiple floors (seen in the wild with `bt003` appearing on both floors 2 and 3 with identical data). When flattening the list, deduplicate by `bt_name` — first occurrence wins.

> **Note on `time_remaining` accuracy:** The value is set when a cycle starts and is **not** a live countdown — it decays as time passes but may drift. Pair it with `start_time` to compute an estimated completion time rather than relying on `time_remaining` alone.

---

## Account Balance

### `GET /account_balance`

Return the current account balance. **Requires authentication.**

**Response (200 OK):**

```json
{
  "account_balance": 1175
}
```

| Field | Type | Description |
|-------|------|-------------|
| `account_balance` | integer | Balance in cents |

> Note: The login response returns `account_balance` as a string; this endpoint returns it as an integer.

**Error responses:**

- `HTTP 401` / `HTTP 403` — Missing or invalid Bearer token.

---

## User Token (Secondary API)

### `POST /get_token`

Obtain a `user_token` for use with the secondary `www.getwashconnect.com` API. **Requires authentication.**

**Request body (JSON):**

```json
{
  "user_id": "595122",
  "uuid": "ffffffff00000000"
}
```

| Field | Description |
|-------|-------------|
| `user_id` | Numeric user ID string from the login response |
| `uuid` | Device UUID — an opaque identifier; the API treats it as a stable device fingerprint |

**Response (200 OK):**

```json
{
  "user_token": "eyJ..."
}
```

The `user_token` is a separate credential from the Bearer token returned by `/login`. It is used for the secondary `www.getwashconnect.com/api/` endpoints (account details, auto-refill settings). Those endpoints are not currently implemented in this integration.

**Error responses:**

- `HTTP 401` / body `status: 401` — Invalid Bearer token or mismatched `user_id`.

---

## Error Handling

All Firebase endpoints return JSON. Non-2xx responses are typically plain HTTP errors. Some endpoints also embed an error status in the response body:

```json
{
  "status": 401,
  "message": "Unauthorized"
}
```

| Condition | Mapped exception |
|-----------|-----------------|
| HTTP 401 / 403 | `AuthError` |
| HTTP 400 on `/login` | `AuthError` (server uses 400 for bad credentials) |
| Body `status: 401` | `AuthError` |
| Any other non-2xx | `ApiError` |
| Body `status` present and not 200/`"ok"` | `ApiError` |

---

## Web API Key

The app bundles a hardcoded web API key used for Firebase Installations and related Google services:

```
AIzaSyA0DfdE2BvRiYKJUgAFtdDSbdZAGyUEJyg
```

This is a public client-side key embedded in the APK — not a server secret. It is not required for any of the Firebase Cloud Functions endpoints described above.

A separate opaque key is also present in the app binary for the secondary API:

```
gc8g4so8c0swo4cock0gckgkck844gg0skk8ooc0
```
