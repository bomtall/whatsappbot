import polars as pl
import requests
import dotenv
import os
import json
from pathlib import Path
import datetime as dt
import time
from typing import Union
from typing import TypedDict

dotenv.load_dotenv()


class Environ(TypedDict):
    repo: Path
    chatId: str
    key: str
    instanceId: str
    group: bool
    
def initialise() -> Environ:
    """Initialise the environment variables and paths.
    """
    environ = Environ(
        repo = Path(os.environ.get("REPO_PATH", "")),
        chatId = os.environ.get("TEST_CHAT_ID", ""),
        # chatId = os.environ.get("CHAT_ID", ""),
        key = os.environ.get("GREEN_API_KEY", ""),
        instanceId = os.environ.get("GREEN_API_INSTANCE_ID", ""),
        group = True
    )
    return environ


def send_message(message: str, key: str, chatId: str, instanceId: str, group: bool) -> bool:
    """Send a message to a WhatsApp chat using the Green API.

    Args:
        message (str): _description_
        key (str): _description_
        chatId (str): _description_
        instanceId (str): _description_
        group (bool): _description_

    Returns:
        bool: Returns True if the message was sent successfully, False otherwise.
    """
    url = f"https://7105.api.greenapi.com/waInstance{instanceId}/sendMessage/{key}"
    
    suffix = "@g.us" if group else "@c.us"
    chatId = chatId + suffix

    payload = {
    "chatId": chatId, 
    "message": message, 
    } 

    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.post(url, json=payload, headers=headers)

    print(response.text.encode('utf8'))
    
    return True

def send_image(image_path: Path, key: str, chatId: str, instanceId: str, group: bool) -> bool:
    """Send an image to a WhatsApp chat using the Green API.

    Args:
        image_path (Path): _description_
        key (str): _description_
        chatId (str): _description_
        instanceId (str): _description_
        group (bool): _description_

    Returns:
        bool: Returns True if the image was sent successfully, False otherwise.
    """
    url = f"https://7105.media.greenapi.com/waInstance{instanceId}/sendFileByUpload/{key}"
    payload = {
    'chatId': chatId + ("@g.us" if group else "@c.us"),
    }
    files = [
    ('file', (image_path.stem + image_path.suffix, open(image_path,'rb'),'image/jpeg'))
    ]
    # headers= {}

    response = requests.post(url, data=payload, files=files)

    print(response.text.encode('utf8'))
    return True

def message_loop(environ: Environ, data_path: Union[Path, str]) -> None:
    """Check message timestamps and send when due.
    
    Args:
        environ (Environ): The environment variables and paths.
        data_path (Union[Path, str], optional): The path to the JSON file containing messages.
    """  
    with open(data_path, "r") as file:
        data = json.load(file)
    now = dt.datetime.now()
    for msg in data["messages"]:
        timestamp = dt.datetime.fromisoformat(msg["timestamp"])
        if not msg["sent"] and timestamp < now:
            
            if send_message(msg["text"], environ["key"], environ["chatId"], environ["instanceId"], environ["group"]):
                    
                if msg["image"]:
                    if send_image(environ["repo"] / f'images/{msg["image"]}', environ["key"], environ["chatId"], environ["instanceId"], environ["group"]):
                        print(f"Sent image: {msg['image']}")
                        msg["sent"] = True
                else:
                    msg["sent"] = True
                        
                with open(data_path, "w") as file:
                    json.dump(data, file, indent=4)
        

if __name__ == "__main__":
    
    environ = initialise()
    data_path = environ["repo"] / "data/messages_test.json"
    
    while True:
        message_loop(environ, data_path)
        time.sleep(300)  # Wait for 5 minutes before checking again

