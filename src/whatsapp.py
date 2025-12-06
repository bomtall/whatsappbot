import requests
import os
from pathlib import Path

def send_message(message: str, chatId: str) -> None:
    """Send a message to a WhatsApp chat using the Green API.
    """
    
    api_instance = os.environ.get("GREEN_API_INSTANCE_ID", "")
    api_key = os.environ.get("GREEN_API_KEY", "")
    message_url = f"https://7105.api.greenapi.com/waInstance{api_instance}/sendMessage/{api_key}"
    
    # Send a message with the location details
    payload = {
        "chatId": chatId, 
        "message": message, 
    } 

    headers = {'Content-Type': 'application/json'}

    response = requests.post(message_url, json=payload, headers=headers)
    print(response.text.encode('utf8'))
    return

def send_location(details: dict, chatId: str) -> None:
    """Send a location to a WhatsApp chat using the Green API.
    """
    
    api_instance = os.environ.get("GREEN_API_INSTANCE_ID", "")
    api_key = os.environ.get("GREEN_API_KEY", "")
    location_url = f"https://7105.api.greenapi.com/waInstance{api_instance}/sendLocation/{api_key}"
    
    payload = {
    "chatId": chatId, 
    "nameLocation": details.get("nameLocation", ""), 
    "address": details.get("address", ""), 
    "latitude": details['latitude'], 
    "longitude": details['longitude']
    }
    headers = {
    'Content-Type': 'application/json'
    }
    response = requests.post(location_url, json=payload, headers=headers)
    print(response.text.encode('utf8'))
    
    return