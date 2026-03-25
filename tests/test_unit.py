"""
Pure-Python unit tests — no HA fixtures needed.

Covers the small helper functions whose correctness isn't obvious from inspection:
  - coordinator.flatten_machines
  - sensor.parse_dt
  - sensor.estimated_completion
"""
import pytest
from datetime import datetime, timedelta, timezone

UTC = timezone.utc

from custom_components.wash_connect.helpers import (
    estimated_completion,
    flatten_machines,
    parse_dt,
)


# ---------------------------------------------------------------------------
# flatten_machines
# ---------------------------------------------------------------------------


def testflatten_machines_adds_floor_name():
    floors = {
        "1": {
            "name": "1st Floor",
            "machines": [
                {"bt_name": "bt001", "machine_number": "001", "type": "washer"},
            ],
        }
    }
    result = flatten_machines(floors)
    assert result["bt001"]["floor_name"] == "1st Floor"


def testflatten_machines_deduplicates_by_bt_name():
    """The same bt_name appearing in two floors should produce only one entry."""
    floors = {
        "2": {
            "name": "2nd Floor",
            "machines": [{"bt_name": "bt003", "machine_number": "003", "type": "washer"}],
        },
        "3": {
            "name": "3rd Floor",
            "machines": [{"bt_name": "bt003", "machine_number": "003", "type": "washer"}],
        },
    }
    result = flatten_machines(floors)
    assert list(result.keys()) == ["bt003"]
    assert result["bt003"]["floor_name"] == "2nd Floor"  # first occurrence wins


def testflatten_machines_empty():
    assert flatten_machines({}) == {}


def testflatten_machines_multiple_floors():
    floors = {
        "1": {
            "name": "1st Floor",
            "machines": [{"bt_name": "bt001", "machine_number": "001", "type": "washer"}],
        },
        "2": {
            "name": "2nd Floor",
            "machines": [{"bt_name": "bt002", "machine_number": "002", "type": "dryer"}],
        },
    }
    result = flatten_machines(floors)
    assert set(result.keys()) == {"bt001", "bt002"}
    assert result["bt001"]["floor_name"] == "1st Floor"
    assert result["bt002"]["floor_name"] == "2nd Floor"


# ---------------------------------------------------------------------------
# parse_dt
# ---------------------------------------------------------------------------


def testparse_dt_valid():
    dt = parse_dt("2026-03-23T15:05:08.000Z")
    assert dt is not None
    assert dt.tzinfo is not None
    assert dt.year == 2026
    assert dt.month == 3
    assert dt.day == 23


def testparse_dt_empty_string():
    assert parse_dt("") is None


def testparse_dt_invalid_string():
    assert parse_dt("not-a-date") is None


def testparse_dt_returns_utc_aware():
    dt = parse_dt("2026-01-01T00:00:00.000Z")
    assert dt.utcoffset().total_seconds() == 0


# ---------------------------------------------------------------------------
# estimated_completion
# ---------------------------------------------------------------------------


def testestimated_completion_available_machine():
    machine = {"status": "available", "time_remaining": "0"}
    assert estimated_completion(machine) is None


def testestimated_completion_in_use_no_time_remaining():
    machine = {"status": "in_use", "time_remaining": "0"}
    assert estimated_completion(machine) is None


def testestimated_completion_in_use_with_time_remaining():
    machine = {"status": "in_use", "time_remaining": "45"}
    before = datetime.now(UTC)
    result = estimated_completion(machine)
    after = datetime.now(UTC)

    assert result is not None
    assert before + timedelta(minutes=44) < result < after + timedelta(minutes=46)


def testestimated_completion_out_of_service():
    machine = {"status": "out_of_service", "time_remaining": "10"}
    assert estimated_completion(machine) is None
