// roadmap.js - Logic for the roadmap page

console.log("Roadmap page script loaded.");

// --- API Fetching (Simplified from script.js) ---

// Use the authenticatedFetch wrapper from auth.js
/*
async function fetchRoadmapData() {
    // ... implementation removed ...
}
*/

// --- UI Rendering ---
function displayRoadmap(items) {
    const listElement = document.getElementById('roadmap-list');
    const loadingMessage = document.getElementById('roadmap-loading-message');
    const errorMessage = document.getElementById('roadmap-error-message');
    const emptyMessage = document.getElementById('roadmap-empty-message');

    // Hide loading message
    if(loadingMessage) loadingMessage.style.display = 'none';

    if (items === null) {
        // Error case
        if(errorMessage) errorMessage.style.display = 'block';
        if(listElement) listElement.style.display = 'none';
        if(emptyMessage) emptyMessage.style.display = 'none';
        return;
    }
    
    if (!listElement) {
        console.error("Element with id 'roadmap-list' not found.");
        if(errorMessage) errorMessage.textContent = "Error interno: no se encontró el elemento de la lista.";
        if(errorMessage) errorMessage.style.display = 'block';
        return;
    }

    // Clear previous items
    listElement.innerHTML = ''; 
    // Ensure messages are hidden initially
    if(errorMessage) errorMessage.style.display = 'none';
    if(emptyMessage) emptyMessage.style.display = 'none';

    if (items.length === 0) {
        if(emptyMessage) emptyMessage.style.display = 'block';
        listElement.style.display = 'none';
    } else {
        listElement.style.display = ''; // Show list
        items.forEach(item => {
            const listItem = document.createElement('li');
            // Apply similar styling as contest-item for consistency?
            // Or use the simpler style from before?
            // Let's use a simpler style for now, can enhance later.
            listItem.style.padding = "0.5em 0";
            listItem.style.borderBottom = "1px dashed #eee";
            listItem.textContent = `[${item.status}] ${item.text} (ID: ${item.id})`;
            listElement.appendChild(listItem);
        });
        // Remove border from last item
        if (listElement.lastChild) {
            listElement.lastChild.style.borderBottom = 'none';
        }
    }
}

// --- Page Load Logic ---
document.addEventListener('DOMContentLoaded', async () => {
    console.log("Roadmap DOM fully loaded and parsed");
    updateNav(); // Update nav based on login status

    // Roadmap items are public, no need for authenticatedFetch
    // We can use a simpler fetch or reuse authenticatedFetch (it works fine if no token exists)
    const response = await authenticatedFetch('/api/v2/roadmap/items');
    let roadmapItems = null;
    
    if (response.ok) {
        try {
            roadmapItems = await response.json();
        } catch(e) {
            console.error("Error parsing roadmap JSON:", e);
            roadmapItems = null; // Treat parse error as fetch failure
        }
    } else {
         console.error(`Failed to fetch roadmap items: ${response.status}`);
    }
    displayRoadmap(roadmapItems);
}); 