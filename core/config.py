import os
import json

DEFAULT = {
    "workspace": "workspace",
    "model": os.environ.get("OMX_MODEL", "models/gemini-2.0-flash"),
    "temp": 0.1,
    "mobile_mode": True
}



CONFIG_FILE = "config.json"

def load():
    if not os.path.exists(CONFIG_FILE):
        save(DEFAULT)
        return DEFAULT
    return json.load(open(CONFIG_FILE))

def save(cfg):
    json.dump(cfg, open(CONFIG_FILE, "w"), indent=2)
