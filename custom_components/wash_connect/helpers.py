"""
Pure helper functions with no Home Assistant dependencies.

Kept separate so they can be unit-tested without a full HA environment.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

_UTC = timezone.utc


def parse_dt(raw: str) -> datetime | None:
    """Parse an ISO 8601 UTC string (e.g. '2026-03-23T15:05:08.000Z') to an aware datetime."""
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def to_int(val: object, default: int = 0) -> int:
    """Convert val to int, returning default on failure."""
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def estimated_completion(machine: dict) -> datetime | None:
    """
    Return the estimated completion time for an in-use machine.

    Returns None when the machine is not in use or has no time remaining.
    """
    remaining = to_int(machine["time_remaining"])
    if remaining <= 0 or machine["status"] != "in_use":
        return None
    return datetime.now(_UTC) + timedelta(minutes=remaining)


def flatten_machines(floors: dict) -> dict[str, dict]:
    """
    Convert the nested floors→machines structure into a flat dict keyed by bt_name.

    Deduplicates by bt_name — the first occurrence wins.
    """
    result: dict[str, dict] = {}
    for floor in floors.values():
        for machine in floor["machines"]:
            bt_name = machine["bt_name"]
            if bt_name not in result:
                result[bt_name] = {**machine, "floor_name": floor["name"]}
    return result
