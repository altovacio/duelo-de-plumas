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
            // Handle delete button clicks
            if (e.target.classList.contains('delete-btn')) {
                const card = e.target.closest('.card');
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
            .then(response => response.json())
            .then(items => {
                // Clear the current items
                Object.values(columns).forEach(column => {
                    const container = column.querySelector('.cards-container');
                    container.innerHTML = '';
                });
                
                // Add the items to their respective columns
                items.forEach(item => {
                    addItemToDOM(item);
                });
            })
            .catch(error => console.error('Error loading roadmap items:', error));
    }
    
    function updateItemStatus(itemId, newStatus) {
        // First find the current item to get its text
        fetch('/api/roadmap/items')
            .then(response => response.json())
            .then(items => {
                const item = items.find(item => item.id === itemId);
                if (item) {
                    // Update the item's status
                    item.status = newStatus;
                    
                    // Send the updated list to the server
                    return fetch('/api/roadmap/items', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(items)
                    });
                }
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    console.error('Failed to update item status');
                    loadRoadmapItems(); // Reload in case of error
                }
            })
            .catch(error => {
                console.error('Error updating item status:', error);
                loadRoadmapItems(); // Reload in case of error
            });
    }
    
    function addNewItem(text) {
        const newItem = {
            text: text,
            status: 'backlog' // New items start in backlog
        };
        
        fetch('/api/roadmap/item', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(newItem)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadRoadmapItems(); // Reload to get the new item with its ID
            }
        })
        .catch(error => console.error('Error adding new item:', error));
    }
    
    function deleteItem(itemId) {
        fetch(`/api/roadmap/item/${itemId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the item from the DOM
                const card = document.querySelector(`.card[data-id="${itemId}"]`);
                if (card) {
                    card.remove();
                }
            }
        })
        .catch(error => console.error('Error deleting item:', error));
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