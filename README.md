# WASH Connect

A [Home Assistant](https://www.home-assistant.io/) custom integration for [WASH Connect](https://www.wash.com) — the laundry management service found in apartments, dormitories, and multi-unit buildings.

## Features

This integration polls the WASH Connect cloud API and exposes the following entities for each laundry machine in your configured location:

| Entity | Type | Description |
|---|---|---|
| Status | Sensor | Current machine state (`available`, `in_use`, etc.) |
| Available | Binary Sensor | `on` when the machine is free to use |
| Time Remaining | Sensor | Minutes left in the current cycle |
| Start Time | Sensor | Timestamp when the current cycle began |
| Estimated Completion | Sensor | Projected finish time for the current cycle |
| BT Name | Sensor (diagnostic) | Bluetooth identifier for the machine |
| Account Balance | Sensor | Your WASH Connect account balance in cents |

## Use Cases

- **Laundry-done notifications** — trigger a mobile push notification or announcement on a smart speaker the moment your machine's status flips from `in_use` to `available`.
- **Building laundry room dashboard** — build a Lovelace card showing which washers and dryers are free right now, so you don't have to walk downstairs to check.
- **Cycle countdown** — display a live timer on a dashboard or a smart display using the *Time Remaining* and *Estimated Completion* sensors.
- **Low-balance alerts** — get notified when your account balance drops below a threshold so you're never caught without funds mid-cycle.
- **Laundry usage automation** — log cycle start/end times to track how often machines are used, or automatically turn on a light in your apartment when your laundry is done.

## Installation

### HACS (recommended)

1. Open HACS → **Integrations** → three-dot menu → **Custom repositories**.
2. Add `https://github.com/yostinso/wash-connect` as an **Integration**.
3. Search for **WASH Connect** and install it.
4. Restart Home Assistant.

### Manual

1. Copy the `custom_components/wash_connect` directory into your HA `config/custom_components/` folder.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **WASH Connect**.
3. Enter your WASH Connect app credentials (email and password).
4. Select your laundry location.

## Requirements

- Home Assistant 2024.1.0 or newer
- An active WASH Connect account

## License

[MIT](LICENSE)
