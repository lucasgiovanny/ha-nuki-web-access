"""Constants for Nuki Web Access."""

from datetime import timedelta

DOMAIN = "nuki_web_access"
API_URL = "https://api.nuki.io"
SCAN_INTERVAL = timedelta(minutes=5)

# Only keypad codes are managed; app users, fobs and the keypad device itself are left alone.
AUTH_TYPE_KEYPAD_CODE = 13
