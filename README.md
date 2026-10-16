# Nuki Web Access

Manage the keypad codes of your Nuki smart lock from Home Assistant: switch a code on or off, give it a date window, or limit it to some weekdays and hours. Handy for codes you hand out — a cleaner who comes on Tuesdays, a pet sitter while you travel — driven by a calendar or any other automation.

It talks to the [Nuki Web API](https://web.nuki.io) and does nothing else. Locking and unlocking are left to your local integration (MQTT, Matter or the Bridge), and app users, fobs and the keypad itself are not touched.

## Installation

1. In HACS, add this repository as a custom repository (category **Integration**) and download **Nuki Web Access**.
2. Restart Home Assistant.
3. At [web.nuki.io](https://web.nuki.io), activate Nuki Web and open **API → Generate API token**. Grant only **View devices** and **View and manage authorizations**.
4. **Settings → Devices & services → Add integration → Nuki Web Access**, and paste the token.

## Entities

Each smart lock gets one device with three entities per keypad code:

| Entity | What it does |
|---|---|
| `switch.<lock>_keypad_codes_<code>_enabled` | Whether the code, and the fingerprints attached to it, open the door. |
| `datetime.<lock>_keypad_codes_<code>_valid_from` | The code works from this moment. Unknown means no start limit. |
| `datetime.<lock>_keypad_codes_<code>_valid_until` | The code stops working at this moment. Unknown means no end limit. |

The switch also shows the code's weekdays, daily hours, last use, number of fingerprints and whether Nuki is still syncing a change to the lock. Its `auth_id` attribute is the id the lock reports for this code in its own lock action events (for example over MQTT), so automations can tell who opened the door.

Codes created later in the Nuki app show up on the next poll, every 5 minutes.

## Action: `nuki_web_access.set_access`

Changes several limits of one code at once. Every field is optional.

```yaml
action: nuki_web_access.set_access
target:
  entity_id: switch.main_door_keypad_codes_cleaners_enabled
data:
  enabled: true
  valid_from: "2026-10-20 07:30:00"
  valid_until: "2026-10-20 15:00:00"
  weekdays: [tue]
  from_time: "07:30:00"
  until_time: "15:00:00"
```

`no_date_limit: true` removes both dates. Times of `00:00` to `00:00` mean all day.

## How changes are applied

Nuki Web sometimes answers a change as accepted without storing it. Every change is therefore read back from Nuki Web, sent a second time if it is not there, and reported as an error if it still is not. Nuki then syncs the code to the lock on its own; the switch's `pending_sync` attribute is on until that has happened.
