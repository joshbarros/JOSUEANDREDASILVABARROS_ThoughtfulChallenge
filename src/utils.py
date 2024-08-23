import json
import os

def load_work_item(config_path):
    with open(config_path, "r") as file:
        return json.load(file)

def get_config():
    config_path = os.getenv("ROBOT_CONFIG", "devdata/workitems/work-item.json")
    return load_work_item(config_path)
