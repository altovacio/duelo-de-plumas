import json
import os
from pathlib import Path
import threading

# File to store roadmap items
ROADMAP_FILE = Path(os.path.dirname(os.path.abspath(__file__))) / 'roadmap_items.json'
# Lock for ensuring atomic file operations
_file_lock = threading.Lock()

# Initialize with default items if file doesn't exist
DEFAULT_ITEMS = [
    {"id": 1, "text": "Improve AI writers (langgraph)", "status": "backlog"},
    {"id": 2, "text": "Improve AI judges (langgraph)", "status": "backlog"},
    {"id": 3, "text": "Improve admin flow", "status": "backlog"},
    {"id": 4, "text": "Improve date deadlines for contests", "status": "backlog"},
    {"id": 5, "text": "User registry with email?", "status": "backlog"},
    {"id": 6, "text": "Improve aesthetics", "status": "backlog"},
    {"id": 7, "text": "Migrate to PostgreSQL?", "status": "backlog"}
]

def _ensure_file_exists():
    """Ensure the roadmap file exists, create with defaults if it doesn't"""
    if not ROADMAP_FILE.exists():
        try:
            with open(ROADMAP_FILE, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_ITEMS, f, indent=2, ensure_ascii=False)
        except IOError as e:
            # Handle potential error during initial file creation
            print(f"Error creating roadmap file: {e}")

def _read_items():
    """Reads items from the JSON file."""
    _ensure_file_exists()
    try:
        with open(ROADMAP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading roadmap file: {e}")
        # Return default items or an empty list in case of read error
        # to prevent crashing the application.
        return list(DEFAULT_ITEMS) # Return a copy

def _write_items(items):
    """Writes items to the JSON file."""
    try:
        with open(ROADMAP_FILE, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error writing roadmap file: {e}")

def get_roadmap_items():
    """Get all roadmap items (thread-safe read)."""
    with _file_lock:
        return _read_items()

def update_single_item_status(item_id, new_status):
    """Update the status of a single roadmap item (atomic operation)."""
    with _file_lock:
        items = _read_items()
        item_found = False
        for item in items:
            if item.get('id') == item_id:
                item['status'] = new_status
                item_found = True
                break
        if item_found:
            _write_items(items)
        return item_found # Indicate if the update was successful

def add_roadmap_item(item_data):
    """Add a new roadmap item (atomic operation)."""
    with _file_lock:
        items = _read_items()

        # Generate a new ID
        max_id = max([i.get('id', 0) for i in items], default=0)
        new_item = {
            'id': max_id + 1,
            'text': item_data.get('text', 'New Item'), # Get text from input dict
            'status': item_data.get('status', 'backlog') # Get status, default backlog
        }

        items.append(new_item)
        _write_items(items)
    # Return the newly created item (including its generated ID)
    return new_item

def delete_roadmap_item(item_id):
    """Delete a roadmap item by ID (atomic operation)."""
    with _file_lock:
        items = _read_items()
        initial_length = len(items)
        items = [item for item in items if item.get('id') != item_id]
        item_deleted = len(items) < initial_length
        if item_deleted:
            _write_items(items)
        return item_deleted # Indicate if deletion occurred 