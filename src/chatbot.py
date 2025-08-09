from whatsapp_chatbot_python import GreenAPIBot, Notification
import dotenv
import os
import json
from pathlib import Path
import re
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import pytz
import train # Import the train module to handle train information

dotenv.load_dotenv()

def convert_to_uk_timestamp_str(timestamp_str: str):
    utc_dt = datetime.fromisoformat(timestamp_str)
    uk_tz = pytz.timezone('Europe/London')
    uk_dt = utc_dt.astimezone(uk_tz)
    formatted_time = uk_dt.strftime('%d/%m/%Y %H:%M')
    return formatted_time

instance=os.environ.get("GREEN_API_INSTANCE_ID", "")
key = os.environ.get("GREEN_API_KEY", "")
repo_path = Path(os.environ.get("REPO_PATH", ""))
train_token = os.environ.get("DARWIN_LITE_TOKEN", "")

bot = GreenAPIBot(instance, key)


def send_location(details: dict, chatId: str) -> None:
    """Send a location to a WhatsApp chat using the Green API.
    """
    api_instance = os.environ.get("GREEN_API_INSTANCE_ID", "")
    api_key = os.environ.get("GREEN_API_KEY", "")
    location_url = f"https://7105.api.greenapi.com/waInstance{api_instance}/sendLocation/{api_key}"
    message_url = f"https://7105.api.greenapi.com/waInstance{api_instance}/sendMessage/{api_key}"
    payload = {
    "chatId": chatId, 
    "nameLocation": "", 
    "address": "", 
    "latitude": details['latitude'], 
    "longitude": details['longitude']
    }
    headers = {
    'Content-Type': 'application/json'
    }
    response = requests.post(location_url, json=payload, headers=headers)
    print(response.text.encode('utf8'))
    
    message = f"Tom's current approximate location:\n\n- Latitude: {details['latitude']:.6f}\n- Longitude: {details['longitude']:.6f}\n- Timestamp: {convert_to_uk_timestamp_str(details['deviceTime'])}\n- Altitude: {details['altitude']}m\n- Speed: {float(details['speed'])*1.852:.2f}\n- Battery Level: {details['attributes']['batteryLevel']}%"
    # Send a message with the location details
    payload = {
        "chatId": chatId, 
        "message": message, 
    } 

    headers = {'Content-Type': 'application/json'}

    response = requests.post(message_url, json=payload, headers=headers)
    print(response.text.encode('utf8'))
    return


train_stops_message = f"""
To get train info, message train followed by the three-letter station code, e.g. 'train HDW' for Hadley Wood.
Here are the codes for our train line:
{'\n'.join([f"{code}: {name}" for code, name in train.our_train.stops.items()])}
"""
    
@bot.router.outgoing_message(text_message=["train", "Train", "trains", "Trains"])
def train_out_message_handler(notification: Notification) -> None:
    notification.answer(train_stops_message)
    return

@bot.router.message(text_message=["train", "Train", "trains", "Trains"])
def train_message_handler(notification: Notification) -> None:
    notification.answer(train_stops_message)
    return

def get_crs_code_from_message(message: str) -> str:
    crs_code = message.strip()[-3:].upper()
    if crs_code not in train.our_train.stops.keys():
        raise ValueError(f"Invalid CRS code: {crs_code}. Please use a valid three-letter station code.")
    return crs_code


@bot.router.outgoing_message(regexp=r"(?i)train\s+[A-Za-z]{3}$", regexp_flags=re.IGNORECASE)
def train_crs_out_message_handler(notification: Notification) -> None:
    crs_code = get_crs_code_from_message(notification.message_text)
    if crs_code != "HDW":
        filter_crs = "HDW"
    else:
        filter_crs = None
    info = train.get_departure_board(crs_code, train_token, 10, filter_crs=filter_crs)
    if not info[2]:
        notification.answer("No train information available at the moment.")
        return
    train_text = train.print_train_info(services=info[2], location_name=info[0], timestamp=info[1])
    notification.answer(train_text)
    
    return

@bot.router.message(regexp=r"(?i)^train\s+[A-Za-z]{3}$", regexp_flags=re.IGNORECASE)
def train_crs_message_handler(notification: Notification) -> None:
    crs_code = get_crs_code_from_message(notification.message_text)
    if crs_code != "HDW":
        filter_crs = "HDW"
    else:
        filter_crs = None
    info = train.get_departure_board(crs_code, train_token, 10, filter_crs=filter_crs)
    if not info[2]:
        notification.answer("No train information available at the moment.")
        return
    train_text = train.print_train_info(services=info[2], location_name=info[0], timestamp=info[1])
    notification.answer(train_text)
    
    return


@bot.router.message(regexp=r"(?i)where(?:\s+is|['’‘ʼ]?s)?\s+tom")
def where_is_tom_handler(notification: Notification) -> None:
    """Handle incoming messages asking about Tom's location.
    Args:
        notification (Notification): The notification object containing message details.
    """

    TRACCAR_USERNAME = os.environ.get("TRACCAR_USERNAME", "")
    TRACCAR_PASSWORD = os.environ.get("TRACCAR_PASS", "")
    TRACCAR_DEVICE_ID = os.environ.get("TRACCAR_DEVICE_ID", "")
    #TRACCAR_URL = 'https://demo.traccar.org'
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
    
    # Send location to WhatsApp chat
    chat_id = notification.chat
    send_location(details, chat_id)


@bot.router.outgoing_message(regexp=r"(?i)where(?:\s+is|['’‘ʼ]?s)?\s+tom")
def where_is_tom_handler(notification: Notification) -> None:
    """Handle incoming messages asking about Tom's location.
    Args:
        notification (Notification): The notification object containing message details.
    """

    TRACCAR_USERNAME = os.environ.get("TRACCAR_USERNAME", "")
    TRACCAR_PASSWORD = os.environ.get("TRACCAR_PASS", "")
    TRACCAR_DEVICE_ID = os.environ.get("TRACCAR_DEVICE_ID", "")
    #TRACCAR_URL = 'https://demo.traccar.org'
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
    
    # Send location to WhatsApp chat
    chat_id = notification.chat
    send_location(details, chat_id)

if __name__ == "__main__":
    # Start the bot
    print("Bot is running...")
    bot.run_forever()