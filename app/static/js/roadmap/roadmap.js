/**
 * Roadmap Board Manager
 * Handles the roadmap board with drag-and-drop functionality and API interactions
 */
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const board = document.getElementById('board');
    const addButton = document.getElementById('add-item-btn');
    const modalOverlay = document.getElementById('modal-overlay');
    const modalForm = document.getElementById('add-item-form');
    const modalClose = document.getElementById('modal-close');
    const modalCancel = document.getElementById('modal-cancel');
    
    // Columns and their statuses
    const columns = {
        'backlog': document.getElementById('backlog-column'),
        'in-progress': document.getElementById('in-progress-column'),
        'completed': document.getElementById('completed-column')
    };
    
    let draggedItem = null;
    
    // Load roadmap items from API
    loadRoadmapItems();
    
    // Event listeners for drag and drop
    document.addEventListener('dragstart', handleDragStart);
    document.addEventListener('dragend', handleDragEnd);
    
    // Add event listeners to column containers for drop targets
    Object.keys(columns).forEach(status => {
        const column = columns[status];
        const container = column.querySelector('.cards-container');
        
        container.addEventListener('dragover', e => {
            e.preventDefault();
            const afterElement = getDragAfterElement(container, e.clientY);
            if (draggedItem) {
                if (!afterElement) {
                    container.appendChild(draggedItem);
                } else {
                    container.insertBefore(draggedItem, afterElement);
                }
            }
        });
        
        container.addEventListener('dragenter', e => {
            e.preventDefault();
            container.classList.add('drag-over');
        });
        
        container.addEventListener('dragleave', () => {
            container.classList.remove('drag-over');
        });
        
        container.addEventListener('drop', e => {
            e.preventDefault();
            container.classList.remove('drag-over');
            if (draggedItem) {
                // Update the item status based on the column
                const itemId = parseInt(draggedItem.dataset.id);
                updateItemStatus(itemId, status);
            }
        });
    });
    
    // Add new item button click
    if (addButton) {
        addButton.addEventListener('click', () => {
            modalOverlay.style.display = 'flex';
        });
    }
    
    // Modal close events
    if (modalClose) {
        modalClose.addEventListener('click', () => {
            modalOverlay.style.display = 'none';
        });
    }
    
    if (modalCancel) {
        modalCancel.addEventListener('click', () => {
            modalOverlay.style.display = 'none';
        });
    }
    
    // Form submit for adding new item
    if (modalForm) {
        modalForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const itemText = document.getElementById('new-item-text').value.trim();
            if (itemText) {
                addNewItem(itemText);
                modalForm.reset();
                modalOverlay.style.display = 'none';
            }
        });
    }
    
    // Click handler for the entire board (event delegation)
    if (board) {
        board.addEventListener('click', (e) => {
            // Find the closest ancestor element (itself or a parent) that is a delete button
            const deleteButton = e.target.closest('.delete-btn');

            // Handle delete button clicks robustly
            if (deleteButton) { // Check if a delete button or its child icon was clicked
                const card = deleteButton.closest('.card');
                if (card) {
                    const itemId = parseInt(card.dataset.id);
                    deleteItem(itemId);
                }
            }
        });
    }
    
    // Helper function to determine drag position
    function getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.card:not(.dragging)')];
        
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }
    
    // Drag handlers
    function handleDragStart(e) {
        if (e.target.classList.contains('card')) {
            draggedItem = e.target;
            e.target.classList.add('dragging');
            // Required for Firefox
            e.dataTransfer.setData('text/plain', '');
            e.dataTransfer.effectAllowed = 'move';
        }
    }
    
    function handleDragEnd(e) {
        if (e.target.classList.contains('card')) {
            e.target.classList.remove('dragging');
            draggedItem = null;
        }
    }
    
    // API functions
    function loadRoadmapItems() {
        fetch('/api/roadmap/items')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(items => {
                // Clear the current items
                Object.values(columns).forEach(column => {
                    const container = column.querySelector('.cards-container');
                    if (container) {
                        container.innerHTML = '';
                    }
                });
                
                // Add the items to their respective columns
                items.forEach(item => {
                    addItemToDOM(item);
                });
            })
            .catch(error => console.error('Error loading roadmap items:', error));
    }
    
    function updateItemStatus(itemId, newStatus) {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        fetch(`/api/roadmap/item/${itemId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ status: newStatus })
        })
        .then(response => {
            // Check if the response was successful (status code 200-299)
            if (!response.ok) {
                // Attempt to parse error response if JSON, otherwise use status text
                return response.json().then(err => {
                    throw new Error(err.error || `HTTP error! status: ${response.status}`);
                }).catch(() => {
                    // If response wasn't JSON, throw generic error
                    throw new Error(`HTTP error! status: ${response.status} ${response.statusText}`);
                });
            }
            return response.json(); // Assuming success response might have data
        })
        .then(data => {
            if (!data.success) {
                // This case might not be reached if errors are thrown above,
                // but kept for robustness if backend sends {success: false} on 2xx status.
                console.error('Failed to update item status (API indicated failure)');
                // Optionally reload items here if needed, though the drop operation
                // already visually moved the item. If the PUT failed, we might
                // want to revert the visual change or show an error.
                 alert('Failed to update item status. Please refresh.');
                 loadRoadmapItems(); // Reload to ensure consistency after failure
            }
            // No need to reload on success, the item is already moved visually
            // and the backend is now consistent.
        })
        .catch(error => {
            console.error('Error updating item status:', error);
            // Reload items to revert the visual change since the backend update failed
            alert(`Error updating item: ${error.message}. Reverting change.`);
            loadRoadmapItems();
        });
    }
    
    function addNewItem(text) {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const newItemData = {
            text: text,
            status: 'backlog' // New items always start in backlog
        };
        
        fetch('/api/roadmap/item', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(newItemData)
        })
        .then(response => {
             if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || `HTTP error! status: ${response.status}`);
                }).catch(() => {
                    throw new Error(`HTTP error! status: ${response.status} ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.item) {
                // Instead of adding directly, just reload the list to get the latest state
                // addItemToDOM(data.item); // No longer needed
                loadRoadmapItems(); 
            } else {
                 console.error('Failed to add new item (API indicated failure or missing item data)');
                 alert('Failed to add item. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error adding new item:', error);
            alert(`Error adding item: ${error.message}`);
        });
    }
    
    function deleteItem(itemId) {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        if (!confirm('Are you sure you want to delete this item?')) {
            return; // Abort if user cancels confirmation
        }
        
        fetch(`/api/roadmap/item/${itemId}`, {
            method: 'DELETE',
            headers: {
                 'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                 return response.json().then(err => {
                    throw new Error(err.error || `HTTP error! status: ${response.status}`);
                }).catch(() => {
                    throw new Error(`HTTP error! status: ${response.status} ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Remove the item from the DOM immediately for responsiveness
                const card = document.querySelector(`.card[data-id="${itemId}"]`);
                if (card) {
                    card.remove();
                }
                // Optionally, could call loadRoadmapItems() here too for belt-and-suspenders,
                // but removing directly is usually fine for deletes.
            } else {
                console.error('Failed to delete item (API indicated failure)');
                alert('Failed to delete item. Please refresh and try again.');
            }
        })
        .catch(error => {
            console.error('Error deleting item:', error);
            alert(`Error deleting item: ${error.message}. Please refresh.`);
        });
    }
    
    function addItemToDOM(item) {
        // Create the card element
        const card = document.createElement('div');
        card.classList.add('card');
        card.setAttribute('draggable', 'true');
        card.dataset.id = item.id;
        
        // Create the card content
        card.innerHTML = `
            <div class="card-content">${item.text}</div>
            <div class="card-actions">
                <button class="delete-btn" title="Delete item">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Add the card to the appropriate column
        const status = item.status || 'backlog';
        const column = columns[status];
        if (column) {
            const container = column.querySelector('.cards-container');
            container.appendChild(card);
        }
    }
}); 