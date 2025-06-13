import polars as pl
import requests
import dotenv
import os
import json
from pathlib import Path
import datetime as dt

dotenv.load_dotenv()

repo_path = Path(str(os.environ.get("REPO_PATH")))
key = os.environ.get("GREEN_API_KEY")
message = "this is another test"
chatId = "447519553091"
group = False
instance = os.environ.get("GREEN_API_INSTANCE_ID")


def send_message(message: str, key: str, chatId: str, instanceId: str, group: bool) -> bool:

    url = f"https://7105.api.greenapi.com/waInstance{instanceId}/sendMessage/{key}"
    
    suffix = "@g.us" if group else "@c.us"
    chatId = chatId + suffix

    payload = {
    "chatId": chatId, 
    "message": message, 
    } 
    # "customPreview": {
    # }
    # }
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.post(url, json=payload, headers=headers)

    print(response.text.encode('utf8'))
    return True

if __name__ == "__main__":
    
    while True:
        with open(repo_path / "data/messages_test.json", "r") as file:
            data = json.load(file)
        now = dt.datetime.now()
        for i in data["messages"]:
            timestamp = dt.datetime.fromisoformat(i["timestamp"])
            if not i["sent"] and timestamp < now:
                
                if send_message(i["text"], key, chatId, instance, group):
                    i["sent"] = True
                    with open(repo_path / "data/messages_test.json", "w") as file:
                        json.dump(data, file, indent=4)