## WASH Connect

Monitor your [WASH Connect](https://www.wash.com) laundry machines directly from Home Assistant.

Once configured, each machine in your building appears as a device with sensors for:
- **Availability** — is the machine free right now?
- **Status** — current machine state (available, in use, etc.)
- **Time Remaining** — minutes left in the active cycle
- **Estimated Completion** — projected finish timestamp

Your **account balance** is also tracked as a sensor, so you can automate low-balance alerts.

**Typical automations:** notify when your laundry is done, display a room dashboard showing free machines, alert when your balance is low.
