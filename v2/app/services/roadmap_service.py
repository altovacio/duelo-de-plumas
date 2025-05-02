import json
import os
from pathlib import Path
import threading
import asyncio # Import asyncio for potential async lock later
from typing import List, Dict, Any, Optional

# Define path relative to project root (assuming service file is in v2/app/services)
# Adjust if roadmap_items.json should live elsewhere (e.g., inside v2/ or v2/app/config/)
PROJECT_ROOT = Path(__file__).parent.parent.parent 
ROADMAP_FILE = PROJECT_ROOT / 'roadmap_items.json'

# Lock for ensuring atomic file operations (Keep threading lock for initial migration)
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

# --- Internal Helper Functions ---

def _ensure_file_exists():
    """Ensure the roadmap file exists, create with defaults if it doesn't"""
    if not ROADMAP_FILE.exists():
        try:
            # Create parent directories if they don't exist
            ROADMAP_FILE.parent.mkdir(parents=True, exist_ok=True) 
            with open(ROADMAP_FILE, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_ITEMS, f, indent=2, ensure_ascii=False)
            print(f"Created default roadmap file at: {ROADMAP_FILE}")
        except IOError as e:
            print(f"Error creating roadmap file at {ROADMAP_FILE}: {e}")
        except Exception as e: # Catch other potential errors like permission issues
            print(f"Unexpected error creating roadmap file at {ROADMAP_FILE}: {e}")


def _read_items() -> List[Dict[str, Any]]:
    """Reads items from the JSON file."""
    _ensure_file_exists() # Ensure file exists before reading
    try:
        with open(ROADMAP_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            # Handle empty file case
            if not content:
                print(f"Warning: Roadmap file {ROADMAP_FILE} is empty. Returning defaults.")
                return list(DEFAULT_ITEMS) # Return a copy
            return json.loads(content)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading or parsing roadmap file {ROADMAP_FILE}: {e}. Returning defaults.")
        return list(DEFAULT_ITEMS) # Return a copy
    except Exception as e:
        print(f"Unexpected error reading roadmap file {ROADMAP_FILE}: {e}. Returning defaults.")
        return list(DEFAULT_ITEMS)


def _write_items(items: List[Dict[str, Any]]):
    """Writes items to the JSON file."""
    try:
         # Ensure parent directory exists before writing
        ROADMAP_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ROADMAP_FILE, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error writing roadmap file {ROADMAP_FILE}: {e}")
    except Exception as e:
        print(f"Unexpected error writing roadmap file {ROADMAP_FILE}: {e}")

# --- Public Service Functions ---

# Note: These are kept synchronous for direct migration using threading.Lock
# For better async performance, rewrite using asyncio file I/O (e.g., aiofiles) and asyncio.Lock

def get_roadmap_items() -> List[Dict[str, Any]]:
    """Get all roadmap items (thread-safe read)."""
    with _file_lock:
        return _read_items()

def update_single_item_status(item_id: int, new_status: str) -> bool:
    """Update the status of a single roadmap item (atomic operation)."""
    with _file_lock:
        items = _read_items()
        item_found = False
        for item in items:
            # Ensure 'id' exists and matches
            if isinstance(item, dict) and item.get('id') == item_id:
                item['status'] = new_status
                item_found = True
                break
        if item_found:
            _write_items(items)
        return item_found

def add_roadmap_item(item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Add a new roadmap item (atomic operation). Returns the new item or None on error."""
    # Basic validation
    if not isinstance(item_data, dict) or 'text' not in item_data:
        print("Error adding roadmap item: Invalid item_data format or missing 'text'.")
        return None
        
    with _file_lock:
        items = _read_items()
        
        # Filter out non-dictionary items just in case file got corrupted
        valid_items = [i for i in items if isinstance(i, dict)]

        # Generate a new ID based on valid items
        max_id = max([i.get('id', 0) for i in valid_items if isinstance(i.get('id'), int)], default=0)
        
        new_item = {
            'id': max_id + 1,
            'text': item_data['text'], # Use validated key
            'status': item_data.get('status', 'backlog') 
        }
        
        # Append to the original list (which might contain invalid items read)
        # Or append to valid_items and rewrite? Let's rewrite with only valid items + new
        valid_items.append(new_item) 
        _write_items(valid_items) # Write back potentially cleaned list + new item
        
    return new_item

def delete_roadmap_item(item_id: int) -> bool:
    """Delete a roadmap item by ID (atomic operation)."""
    with _file_lock:
        items = _read_items()
        initial_length = len(items)
        # Ensure we only compare against dictionary items with an 'id'
        items_after_delete = [
            item for item in items 
            if not (isinstance(item, dict) and item.get('id') == item_id)
        ]
        item_deleted = len(items_after_delete) < initial_length
        if item_deleted:
            _write_items(items_after_delete)
        return item_deleted 