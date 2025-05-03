// admin_ai_writers.js - Logic for managing AI Writers

console.log("Admin AI Writers script loaded.");

// --- DOM Elements ---
const loadingMessage = document.getElementById('loading-message');
const errorMessageDiv = document.getElementById('error-message');
const tableContainer = document.getElementById('admin-table-container');
const writersTableBody = document.querySelector('#ai-writers-table tbody');
const noWritersMessage = document.getElementById('no-writers-message');

// --- API Calls ---
async function fetchAIWriters() {
    console.log("Fetching AI writers...");
    const response = await authenticatedFetch('/admin/ai-writers');
    if (!response.ok) {
        throw new Error(`Failed to fetch AI writers: ${response.status}`);
    }
    return response.json();
}

async function deleteAIWriter(writerId) {
    console.log(`Attempting to delete AI writer ${writerId}`);
    const response = await authenticatedFetch(`/admin/ai-writers/${writerId}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
         let detail = `Error ${response.status}`; 
         try { const err = await response.json(); if(err.detail) detail = err.detail; } catch(e){}
        throw new Error(`Failed to delete AI writer: ${detail}`);
    }
    return true; // Success
}

// --- UI Rendering ---
function displayWriters(writers) {
    if (!writersTableBody) return;
    writersTableBody.innerHTML = ''; // Clear previous

    if (!writers || writers.length === 0) {
        if (noWritersMessage) noWritersMessage.style.display = 'block';
        return;
    }
    
    if (noWritersMessage) noWritersMessage.style.display = 'none';

    writers.forEach(writer => {
        const row = writersTableBody.insertRow();
        row.dataset.writerId = writer.id; 
        row.innerHTML = `
            <td>${writer.name}</td>
            <td>${writer.description || '-'}</td>
            <td class="actions-column">
                <a href="/admin_ai_writer_edit.html?id=${writer.id}" class="button button-small button-icon" title="Editar"><i class="fas fa-edit"></i>✏️</a>
                <button class="button button-small button-danger button-icon delete-writer-btn" title="Eliminar"><i class="fas fa-trash"></i>🗑️</button>
            </td>
        `;
    });

    // Add event listeners
    writersTableBody.querySelectorAll('.delete-writer-btn').forEach(button => {
        button.addEventListener('click', handleDeleteClick);
    });
}

// --- Event Handlers ---
async function handleDeleteClick(event) {
    const button = event.target.closest('button');
    const row = button.closest('tr');
    const writerId = row.dataset.writerId;
    const writerName = row.cells[0].textContent;

    if (!writerId) return;

    if (confirm(`¿Estás seguro de que quieres eliminar el escritor IA "${writerName}" (ID: ${writerId})?`)) {
        errorMessageDiv.style.display = 'none'; 
        button.disabled = true;
        try {
            await deleteAIWriter(writerId);
            console.log(`AI Writer ${writerId} deleted.`);
            row.remove();
        } catch (error) {
            console.error("Delete failed:", error);
            errorMessageDiv.textContent = `Error al eliminar: ${error.message}`;
            errorMessageDiv.style.display = 'block';
            button.disabled = false;
        }
    }
}

// --- Page Load Logic ---
document.addEventListener('DOMContentLoaded', async () => {
    // Verify admin role first 
    if (!isLoggedIn()) {
        window.location.href = `/login.html?next=${encodeURIComponent(window.location.pathname)}`;
        return;
    }
    let isAdmin = false;
    try {
        const user = await getUserInfo(); 
        if (user && user.role === 'admin') {
            isAdmin = true;
        } 
    } catch (error) { /* Ignore */ }

    if (!isAdmin) {
        displayAdminError("Acceso denegado. Se requieren permisos de administrador.");
        return;
    }
    
    // Admin verified, load writers
    try {
        const writers = await fetchAIWriters();
        displayWriters(writers);
        if(loadingMessage) loadingMessage.style.display = 'none';
        if(tableContainer) tableContainer.style.display = 'block';
    } catch (error) {
        console.error("Error loading AI writers:", error);
        displayAdminError(`Error al cargar escritores IA: ${error.message}`);
    }
});

function displayAdminError(message) {
    if(loadingMessage) loadingMessage.style.display = 'none';
    if(tableContainer) tableContainer.style.display = 'none'; 
    if(errorMessageDiv) {
        errorMessageDiv.textContent = message;
        errorMessageDiv.style.display = 'block';
    }
} 