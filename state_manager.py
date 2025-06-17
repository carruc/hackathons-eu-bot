# state_manager.py
import json

STATE_FILE = 'posted_hackathons.json'

def load_posted_links():
    """Loads the set of already posted hackathon links from a file."""
    try:
        with open(STATE_FILE, 'r') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or is empty, return an empty set
        return set()

def save_posted_links(links):
    """Saves the set of posted hackathon links to a file."""
    with open(STATE_FILE, 'w') as f:
        json.dump(list(links), f)

