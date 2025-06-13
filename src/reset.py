import os
import json
from pathlib import Path
import dotenv

dotenv.load_dotenv()

repo_path = Path(str(os.environ.get("REPO_PATH")))
   
def reset(file_path: str | Path) -> bool:
    
    with open(repo_path / "data/messages_test.json", "r") as file:
        data = json.load(file)
        
    for i in data["messages"]:
        i["sent"] = False
        
    with open(repo_path / "data/messages_test.json", "w") as file:
        json.dump(data, file, indent=4)
    
    return True
    
    
if __name__ == "__main__":
    
    reset(repo_path / "data/messages_test.json")
    # reset(repo_path / "data/messages.json")
    
    
        