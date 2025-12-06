import requests
import os
from requests.auth import HTTPBasicAuth


def get_location_details() -> dict:
    """Get the latest location details from the API.
    Returns:
        dict: The latest location details.
    """
    TRACCAR_USERNAME = os.environ.get("TRACCAR_USERNAME", "")
    TRACCAR_PASSWORD = os.environ.get("TRACCAR_PASS", "")
    TRACCAR_DEVICE_ID = os.environ.get("TRACCAR_DEVICE_ID", "")
    # TRACCAR_URL = 'https://demo.traccar.org'
    TRACCAR_URL = 'https://server.traccar.org'

    devices_response = requests.get(
        f'{TRACCAR_URL}/api/devices',
        auth=HTTPBasicAuth(TRACCAR_USERNAME, TRACCAR_PASSWORD)
    )

    devices = devices_response.json()

    for device in devices:
        print(f"Device: {device['name']} - ID: {device['id']}")

    device_id = devices[0]['id']

    positions_response = requests.get(
        f'{TRACCAR_URL}/api/positions',
        auth=HTTPBasicAuth(TRACCAR_USERNAME, TRACCAR_PASSWORD)
    )

    positions = positions_response.json()
    print(positions)

    details = {}
    for pos in positions:
        if pos['deviceId'] == device_id:
            details = pos
            # print(f"Device Location: ({latitude}, {longitude}) at {timestamp}")
            break
    
    return details