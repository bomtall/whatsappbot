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


@bot.router.message(text_message=["info", "Info", "information", "Information"])
def message_handler(notification: Notification) -> None:
    """Handle incoming text messages.
    Args:
        notification (Notification): The notification object containing message details.
    """
    notification.answer("""
Hello! Welcome to Thomas & Daria's tenth wedding anniversay celebration group chat!!

Here are some important details:

- Date: Friday 20th June from 17:30 until Sunday 22nd June.

- Location Holly Bush Farm, Pikehall, Matlock DE4 2PH, UK.

- Accommodation is available for all guests.

- Friday night takeaway, Saturday evening meal and Sunday breakfast will be provided.

- Please bring your own drinks, snacks and food for other meals, basic essentials provided.

- The event is BYOB (Bring Your Own Booze).

- Bring your walking boots!

You can also find more information in the guest list by typing 'guestlist' or 'guests' in the chat for the list of attendees or 'walk' for details about the walk on Saturday morning.
""")
    return
    
@bot.router.message(text_message=["guestlist", "Guestlist", "guest list", "Guest List", "guests", "Guests", "Guest list", "guest List"])
def guest_list_message_handler(notification: Notification) -> None:
    """Handle guest list requests.
    Args:
        notification (Notification): The notification object containing message details.
    """
    # This function will be called when a message with the text "guestlist" is received
    with open(repo_path / "data/guest_list.json", "r") as file:
        guest_list = json.load(file)
    notification.answer("\n".join(guest_list["guests"]))
    return

    
@bot.router.message(text_message=["Walk", "walk"])
def walk_message_handler(notification: Notification) -> None:
    """Handle guest list requests.
    Args:
        notification (Notification): The notification object containing message details.
    """
    notification.answer("""
Join us for a lovely walk on Saturday morning at Dovedale!

Meet us at the carpark:

https://maps.app.goo.gl/gP2s2hqpVz7fNVUh9
""")
    return
    
    
# @bot.router.message(text_message=lambda msg: "where is tom" in msg.lower())

@bot.router.message()
def where_is_tom_handler(notification: Notification) -> None:
    """Handle incoming messages asking about Tom's location.
    Args:
        notification (Notification): The notification object containing message details.
    """
    if not notification.message_text:
        return
    incoming_message = notification.message_text.lower()
    pattern =  re.compile(r"where[’'‘ʼ]s\s+tom", re.IGNORECASE)
    if not (
        "where is tom" in incoming_message or 
        pattern.search(incoming_message) or
        "where tom" in incoming_message 
        ):
        return

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