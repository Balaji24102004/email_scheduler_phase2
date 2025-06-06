import json
import os
from datetime import datetime

STATE_FILE = "campaign_state.json"

def initialize_state(start_date, email_series):
    """Create a state file if it doesn't exist."""
    if not os.path.exists(STATE_FILE):
        state = {
            "start_date": start_date,
            "sent_emails": []  # store list of day_offsets that are sent
        }
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)

def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def update_state(day_offset):
    state = load_state()
    if day_offset not in state["sent_emails"]:
        state["sent_emails"].append(day_offset)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)

def get_today_offset():
    state = load_state()
    start_date = datetime.strptime(state["start_date"], "%Y-%m-%d")
    today = datetime.today()
    return (today - start_date).days
