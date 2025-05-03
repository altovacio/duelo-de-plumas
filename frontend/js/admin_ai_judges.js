// admin_ai_judges.js - Logic for managing AI Judges

console.log("Admin AI Judges script loaded.");

// --- DOM Elements ---
const loadingMessage = document.getElementById('loading-message');
const errorMessageDiv = document.getElementById('error-message');
const tableContainer = document.getElementById('admin-table-container');
const judgesTableBody = document.querySelector('#ai-judges-table tbody');
const noJudgesMessage = document.getElementById('no-judges-message');

// --- API Calls ---
async function fetchAIJudges() {
    console.log("Fetching AI judges...");
    const response = await authenticatedFetch('/admin/ai-judges');
    if (!response.ok) {
        throw new Error(`Failed to fetch AI judges: ${response.status}`);
    }
    return response.json();
}

async function deleteAIJudge(judgeId) {
    console.log(`Attempting to delete AI judge ${judgeId}`);
    const response = await authenticatedFetch(`/admin/ai-judges/${judgeId}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
         let detail = `Error ${response.status}`; 
         try { const err = await response.json(); if(err.detail) detail = err.detail; } catch(e){}
        throw new Error(`Failed to delete AI judge: ${detail}`);
    }
    return true; // Success
}

// --- UI Rendering ---
function displayJudges(judges) {
    if (!judgesTableBody) return;
    judgesTableBody.innerHTML = ''; // Clear previous

    if (!judges || judges.length === 0) {
        if (noJudgesMessage) noJudgesMessage.style.display = 'block';
        return;
    }
    
    if (noJudgesMessage) noJudgesMessage.style.display = 'none';

    judges.forEach(judge => {
        const row = judgesTableBody.insertRow();
        row.dataset.judgeId = judge.id; 
        row.innerHTML = `
            <td>${judge.name}</td>
            <td>${judge.description || '-'}</td>
            <td class="actions-column">
                <a href="/admin_ai_judge_edit.html?id=${judge.id}" class="button button-small button-icon" title="Editar"><i class="fas fa-edit"></i>✏️</a>
                <button class="button button-small button-danger button-icon delete-judge-btn" title="Eliminar"><i class="fas fa-trash"></i>🗑️</button>
            </td>
        `;
    });

    // Add event listeners
    judgesTableBody.querySelectorAll('.delete-judge-btn').forEach(button => {
        button.addEventListener('click', handleDeleteClick);
    });
}

// --- Event Handlers ---
async function handleDeleteClick(event) {
    const button = event.target.closest('button');
    const row = button.closest('tr');
    const judgeId = row.dataset.judgeId;
    const judgeName = row.cells[0].textContent;

    if (!judgeId) return;

    if (confirm(`¿Estás seguro de que quieres eliminar el juez IA "${judgeName}" (ID: ${judgeId})?`)) {
        errorMessageDiv.style.display = 'none'; 
        button.disabled = true;
        try {
            await deleteAIJudge(judgeId);
            console.log(`AI Judge ${judgeId} deleted.`);
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
        const user = await getUserInfo(); // Use cached info if available
        if (user && user.role === 'admin') {
            isAdmin = true;
        } 
    } catch (error) { /* Ignore */ }

    if (!isAdmin) {
        displayAdminError("Acceso denegado. Se requieren permisos de administrador.");
        return;
    }
    
    // Admin verified, load judges
    try {
        const judges = await fetchAIJudges();
        displayJudges(judges);
        if(loadingMessage) loadingMessage.style.display = 'none';
        if(tableContainer) tableContainer.style.display = 'block';
    } catch (error) {
        console.error("Error loading AI judges:", error);
        displayAdminError(`Error al cargar jueces IA: ${error.message}`);
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