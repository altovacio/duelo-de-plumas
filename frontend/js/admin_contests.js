// admin_contests.js - Logic for the admin contest management page

console.log("Admin Contests script loaded.");

// --- DOM Elements ---
const loadingMessage = document.getElementById('loading-message');
const errorMessageDiv = document.getElementById('error-message');
const tableContainer = document.getElementById('admin-table-container');
const contestsTableBody = document.querySelector('#contests-table tbody');
const noContestsMessage = document.getElementById('no-contests-message');

// --- Helper Functions ---
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return new Date(dateString).toLocaleDateString(undefined, options);
    } catch (e) {
        return dateString;
    }
}

// --- API Calls ---
async function fetchAllContests() {
    console.log("Fetching all contests for admin...");
    // Admins should get all contests from the main GET /contests endpoint
    const response = await authenticatedFetch('/contests/'); 
    if (!response.ok) {
        throw new Error(`Failed to fetch contests: ${response.status}`);
    }
    return response.json();
}

async function deleteContest(contestId) {
    console.log(`Attempting to delete contest ${contestId}`);
    const response = await authenticatedFetch(`/contests/${contestId}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
         // Try to get error detail
         let detail = `Error ${response.status}`; 
         try { const err = await response.json(); if(err.detail) detail = err.detail; } catch(e){}
        throw new Error(`Failed to delete contest: ${detail}`);
    }
    return true; // Success
}

async function updateContestStatus(contestId, newStatus) {
    console.log(`Attempting to update contest ${contestId} to status ${newStatus}`);
    const response = await authenticatedFetch(`/contests/${contestId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
    });
     if (!response.ok) {
         let detail = `Error ${response.status}`; 
         try { const err = await response.json(); if(err.detail) detail = err.detail; } catch(e){}
        throw new Error(`Failed to update status: ${detail}`);
    }
    return response.json(); // Return updated contest data
}


// --- UI Rendering ---
function displayContests(contests) {
    if (!contestsTableBody) return;
    contestsTableBody.innerHTML = ''; // Clear previous

    if (!contests || contests.length === 0) {
        if (noContestsMessage) noContestsMessage.style.display = 'block';
        return;
    }
    
    if (noContestsMessage) noContestsMessage.style.display = 'none';

    contests.forEach(contest => {
        const row = contestsTableBody.insertRow();
        row.dataset.contestId = contest.id; // Store id for actions
        
        const possibleStatuses = ['draft', 'open', 'evaluation', 'closed']; // Define possible statuses
        let statusOptionsHtml = possibleStatuses.map(s => 
            `<option value="${s}" ${s === contest.status ? 'selected' : ''}>${s}</option>`
        ).join('');

        row.innerHTML = `
            <td><a href="/contest.html?id=${contest.id}">${contest.title}</a></td>
            <td>${contest.contest_type}</td>
            <td>
                 <form class="inline-form status-update-form">
                     <select name="status" class="small-select" data-current-status="${contest.status}">
                         ${statusOptionsHtml}
                     </select>
                     <button type="submit" class="button button-small status-apply-button" disabled>Aplicar</button>
                 </form>
            </td>
            <td>${formatDate(contest.end_date)}</td>
            <td class="actions-column">
                <a href="/admin_contest_edit.html?id=${contest.id}" class="button button-small button-icon" title="Editar"><i class="fas fa-edit"></i>✏️</a>
                <a href="/submissions.html?id=${contest.id}" class="button button-small button-icon" title="Ver Envíos"><i class="fas fa-list"></i>👁️</a>
                <button class="button button-small button-danger button-icon delete-contest-btn" title="Eliminar"><i class="fas fa-trash"></i>🗑️</button>
            </td>
        `;
    });

    // Add event listeners AFTER populating the table
    addTableEventListeners();
}

function addTableEventListeners() {
    contestsTableBody.querySelectorAll('.delete-contest-btn').forEach(button => {
        button.addEventListener('click', handleDeleteClick);
    });
    contestsTableBody.querySelectorAll('.status-update-form select').forEach(select => {
        select.addEventListener('change', handleStatusChange);
    });
     contestsTableBody.querySelectorAll('.status-update-form').forEach(form => {
        form.addEventListener('submit', handleStatusSubmit);
    });
}

// --- Event Handlers ---

function handleStatusChange(event) {
    const select = event.target;
    const applyButton = select.closest('form').querySelector('.status-apply-button');
    const currentStatus = select.dataset.currentStatus;
    // Enable button only if status changed
    applyButton.disabled = (select.value === currentStatus);
}

async function handleStatusSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const select = form.querySelector('select[name="status"]');
    const button = form.querySelector('.status-apply-button');
    const contestId = form.closest('tr').dataset.contestId;
    const newStatus = select.value;

    button.disabled = true;
    button.textContent = '...';
    errorMessageDiv.style.display = 'none'; // Hide previous errors

    try {
        const updatedContest = await updateContestStatus(contestId, newStatus);
        console.log("Status updated:", updatedContest);
        // Update UI: reset select's current status and disable button
        select.dataset.currentStatus = newStatus;
        button.disabled = true;
        button.textContent = 'Aplicar';
        // Optionally show a success flash message
    } catch (error) {
        console.error("Status update failed:", error);
        errorMessageDiv.textContent = `Error al actualizar estado: ${error.message}`;
        errorMessageDiv.style.display = 'block';
        button.textContent = 'Aplicar';
        // Re-enable button based on original state (or just keep disabled on error?)
        // button.disabled = (select.value === select.dataset.currentStatus);
    }
}

async function handleDeleteClick(event) {
    const button = event.target.closest('button');
    const row = button.closest('tr');
    const contestId = row.dataset.contestId;
    const contestTitle = row.cells[0].textContent; // Get title for confirmation

    if (confirm(`¿Estás seguro de que quieres eliminar el concurso "${contestTitle}" (ID: ${contestId})? Esta acción no se puede deshacer.`)) {
        errorMessageDiv.style.display = 'none'; // Hide previous errors
        button.disabled = true;
        try {
            await deleteContest(contestId);
            console.log(`Contest ${contestId} deleted.`);
            row.remove(); // Remove row from table
             // Optionally show a success flash message
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
    // updateNav called by auth.js

    // Verify admin role first (copied from admin.js)
    if (!isLoggedIn()) {
        window.location.href = `/login.html?next=${encodeURIComponent(window.location.pathname)}`;
        return;
    }

    let isAdmin = false;
    try {
        const response = await authenticatedFetch('/auth/users/me');
        if (response.ok) {
            const user = await response.json();
            if (user && user.role === 'admin') {
                isAdmin = true;
            } 
        }
    } catch (error) { /* Ignore */ }

    if (!isAdmin) {
        displayAdminError("Acceso denegado. Se requieren permisos de administrador.");
        return;
    }
    
    // Admin verified, proceed to load contests
    try {
        const contests = await fetchAllContests();
        displayContests(contests);
        if(loadingMessage) loadingMessage.style.display = 'none';
        if(tableContainer) tableContainer.style.display = 'block';
    } catch (error) {
        console.error("Error loading admin contests:", error);
        displayAdminError(`Error al cargar concursos: ${error.message}`);
    }
});

function displayAdminError(message) {
    if(loadingMessage) loadingMessage.style.display = 'none';
    if(tableContainer) tableContainer.style.display = 'none'; // Hide table container on error
    if(errorMessageDiv) {
        errorMessageDiv.textContent = message;
        errorMessageDiv.style.display = 'block';
    }
} 