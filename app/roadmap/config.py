import json
import os
from pathlib import Path

# File to store roadmap items
ROADMAP_FILE = Path(os.path.dirname(os.path.abspath(__file__))) / 'roadmap_items.json'

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
        with open(ROADMAP_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_ITEMS, f, indent=2, ensure_ascii=False)

def get_roadmap_items():
    """Get all roadmap items"""
    _ensure_file_exists()
    with open(ROADMAP_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def update_roadmap_items(items):
    """Update all roadmap items"""
    with open(ROADMAP_FILE, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

def add_roadmap_item(item):
    """Add a new roadmap item"""
    items = get_roadmap_items()
    
    # Generate a new ID
    max_id = max([i.get('id', 0) for i in items], default=0)
    item['id'] = max_id + 1
    
    items.append(item)
    update_roadmap_items(items)
    return item

def delete_roadmap_item(item_id):
    """Delete a roadmap item by ID"""
    items = get_roadmap_items()
    items = [item for item in items if item.get('id') != item_id]
    update_roadmap_items(items) 