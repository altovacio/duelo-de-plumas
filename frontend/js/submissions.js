// submissions.js - Logic for the submission list page

console.log("Submissions page script loaded.");

// --- Helper Functions ---
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        // More detailed format including time
        const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
        return new Date(dateString).toLocaleDateString(undefined, options);
    } catch (e) {
        console.error("Error formatting date:", dateString, e);
        return dateString;
    }
}

// --- DOM Elements ---
const loadingMessage = document.getElementById('loading-message');
const errorMessageDiv = document.getElementById('error-message');
const contentDiv = document.getElementById('submission-list-content');
const contestTitleHeading = document.getElementById('contest-title-heading');
const submissionsTableBody = document.querySelector('#submissions-table tbody');
const noSubmissionsMessage = document.getElementById('no-submissions-message');
const modal = document.getElementById('view-text-modal');
const modalTitle = document.getElementById('modal-submission-title');
const modalText = document.getElementById('modal-text');
const modalCloseBtn = document.getElementById('modal-close-btn');

// Store submission texts temporarily to avoid embedding large texts in HTML
let submissionTexts = {};

// --- Functions ---

function displayError(message) {
    if (loadingMessage) loadingMessage.style.display = 'none';
    if (contentDiv) contentDiv.style.display = 'none';
    if (errorMessageDiv) {
        errorMessageDiv.textContent = message;
        errorMessageDiv.style.display = 'block';
    }
}

function openModal(submissionId) {
    const submission = submissionTexts[submissionId];
    if (submission && modal && modalTitle && modalText) {
        modalTitle.textContent = submission.title;
        // Basic display, consider markdown rendering later if needed
        modalText.textContent = submission.text_content;
        modal.style.display = 'flex';
    } else {
        console.error("Could not find submission text or modal elements for ID:", submissionId);
    }
}

function closeModal() {
    if (modal) {
        modal.style.display = 'none';
    }
}

function displaySubmissions(contestTitle, submissions) {
    if (contestTitleHeading) contestTitleHeading.textContent += contestTitle;
    document.title = `Envíos: ${contestTitle} - Duelo de Plumas`;

    if (!submissionsTableBody) {
        console.error("Submissions table body not found.");
        if (noSubmissionsMessage) noSubmissionsMessage.style.display = 'block';
        return;
    }
    submissionsTableBody.innerHTML = ''; // Clear previous rows
    submissionTexts = {}; // Clear stored texts

    if (!submissions || submissions.length === 0) {
        if (noSubmissionsMessage) noSubmissionsMessage.style.display = 'block';
    } else {
        if (noSubmissionsMessage) noSubmissionsMessage.style.display = 'none';
        submissions.forEach(sub => {
            // Store text content for modal
            submissionTexts[sub.id] = sub;
            
            const row = submissionsTableBody.insertRow();
            row.innerHTML = `
                <td>${sub.author_name}</td>
                <td>${sub.title}</td>
                <td>${formatDate(sub.submission_date)}</td>
                <td class="actions-column">
                    <button class="button button-small view-text-btn" data-submission-id="${sub.id}">Ver Texto</button>
                    <!-- Add Evaluate/Delete buttons later if needed -->
                    <!-- Add Delete Button (conditionally for admin?) -->
                    <button class="button button-small button-danger button-icon delete-submission-btn" data-submission-id="${sub.id}" title="Eliminar Envío">
                         <i class="fas fa-trash"></i>🗑️
                     </button>
                </td>
            `;
        });
        
        // Add event listeners for view buttons
        document.querySelectorAll('.view-text-btn').forEach(button => {
            button.addEventListener('click', (event) => {
                const subId = event.target.dataset.submissionId;
                openModal(subId);
            });
        });
        // Add event listeners for delete buttons
        document.querySelectorAll('.delete-submission-btn').forEach(button => {
            button.addEventListener('click', handleDeleteSubmissionClick);
        });
    }
    
    // Show content
    if (loadingMessage) loadingMessage.style.display = 'none';
    if (contentDiv) contentDiv.style.display = 'block';
}

// --- Add Delete Submission Handler ---
async function handleDeleteSubmissionClick(event) {
    const button = event.target.closest('button');
    const submissionId = button.dataset.submissionId;
    const row = button.closest('tr');
    const submissionTitle = row.cells[1].textContent; // Get title for confirmation

    if (!submissionId) return;

    if (confirm(`¿Estás seguro de que quieres eliminar el envío "${submissionTitle}" (ID: ${submissionId})?`)) {
        // Hide previous errors shown maybe at the top of the page?
        // const topError = document.getElementById('error-message'); 
        // if (topError) topError.style.display = 'none';
        
        button.disabled = true;
        try {
            console.log(`Attempting delete submission ${submissionId}`);
            const response = await authenticatedFetch(`/admin/submissions/${submissionId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                let detail = `Error ${response.status}`;
                try { const err = await response.json(); if(err.detail) detail = err.detail; } catch(e){}
                throw new Error(`Failed to delete submission: ${detail}`);
            }
            
            console.log(`Submission ${submissionId} deleted.`);
            row.remove(); // Remove the row from the table
            // Optionally show a temporary success message
            
        } catch (error) {
            console.error("Delete submission failed:", error);
            // Display error message (maybe near the button or at the top?)
            alert(`Error al eliminar envío: ${error.message}`); // Simple alert for now
            button.disabled = false;
        }
    }
}

// --- Page Load Logic ---
document.addEventListener('DOMContentLoaded', async () => {
    updateNav(); // Update nav based on login status
    
    const params = new URLSearchParams(window.location.search);
    const contestId = params.get('id');

    if (!contestId) {
        displayError("No se especificó un ID de concurso en la URL.");
        return;
    }

    console.log(`Fetching details for contest ID: ${contestId}`);
    // We MUST be logged in and authorized (judge/admin) to see this page
    if (!isLoggedIn()) {
        // Redirect to login, maybe pass current URL as 'next' param
        window.location.href = `/login.html?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
        return;
    }
    
    const response = await authenticatedFetch(`/contests/${contestId}`);

    if (response.ok) {
        try {
            const contestData = await response.json();
            console.log("Contest data fetched:", contestData);
            // Check if contest is in evaluation or closed - otherwise maybe show error?
            if (contestData.status === 'evaluation' || contestData.status === 'closed') {
                 displaySubmissions(contestData.title, contestData.submissions);
            } else {
                displayError(`Error: Los envíos solo se pueden ver durante la evaluación o después del cierre (Estado actual: ${contestData.status}).`);
            }
        } catch (e) {
            console.error("Error parsing contest data JSON:", e);
            displayError("Error al procesar los datos del concurso.");
        }
    } else {
        let errorMsg = `Error ${response.status}: Error desconocido al cargar los envíos.`;
        if (response.status === 404) {
            errorMsg = "Error 404: Concurso no encontrado.";
        } else if (response.status === 403) {
            errorMsg = "Error 403: No tienes permiso para ver los envíos de este concurso.";
        } else if (response.status === 401) {
             errorMsg = "Error 401: Sesión inválida o expirada. Por favor, inicia sesión de nuevo.";
             // Optionally redirect to login
             // window.location.href = `/login.html?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
        }
        try {
             const errorResult = await response.json();
             if (errorResult && errorResult.detail) { errorMsg += ` (${errorResult.detail})`; }
        } catch(e) { /* Ignore JSON parse error */ }
        
        displayError(errorMsg);
    }
    
    // Modal close functionality
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', closeModal);
    }
    // Close modal if clicking outside the content
    if (modal) {
        modal.addEventListener('click', (event) => {
            if (event.target === modal) { // Check if the click was on the overlay itself
                closeModal();
            }
        });
    }
}); 