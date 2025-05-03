// admin_ai_submission.js - Logic for triggering AI submissions

console.log("Admin AI Submission script loaded.");

// --- DOM Elements ---
const loadingMessage = document.getElementById('loading-message');
const errorMessageDiv = document.getElementById('error-message');
const successMessageDiv = document.getElementById('success-message');
const submissionForm = document.getElementById('ai-submission-form');
const contestSelect = document.getElementById('contest-select');
const writerSelect = document.getElementById('writer-select');
const modelSelect = document.getElementById('model-select');
const titleInput = document.getElementById('title');
const submitButton = document.getElementById('submit-button');

// --- Helper Functions ---
function displayError(message) {
    if(loadingMessage) loadingMessage.style.display = 'none';
    if(submissionForm) submissionForm.style.display = 'block'; // Keep form visible
    if(errorMessageDiv) {
        errorMessageDiv.textContent = message;
        errorMessageDiv.style.display = 'block';
        successMessageDiv.style.display = 'none';
    }
}

function displaySuccess(message) {
    if(errorMessageDiv) errorMessageDiv.style.display = 'none';
    if(successMessageDiv) {
        successMessageDiv.textContent = message;
        successMessageDiv.style.display = 'block';
    }
    // Optionally clear form or disable button after success?
    // submissionForm.reset();
    // if(submitButton) submitButton.disabled = true;
}

// --- API Calls ---
async function fetchOpenContests() {
    console.log("Fetching open contests...");
    // Assuming /contests/ lists all, we need to filter client-side or add API filter
    const response = await authenticatedFetch('/contests/'); 
    if (!response.ok) throw new Error(`Failed to fetch contests: ${response.status}`);
    const allContests = await response.json();
    // Filter for contests with status 'open'
    return allContests.filter(contest => contest.status === 'open');
}

async function fetchAIWriters() {
    console.log("Fetching AI writers...");
    const response = await authenticatedFetch('/admin/ai-writers');
    if (!response.ok) throw new Error(`Failed to fetch AI writers: ${response.status}`);
    return response.json();
}

// TODO: Fetch available AI Models dynamically if possible?
// For now, they are hardcoded in the HTML.

async function triggerAISubmission(contestId, writerId, modelId, title) {
    console.log(`Triggering AI submission for contest ${contestId} by writer ${writerId} using ${modelId}`);
    const payload = {
        ai_writer_id: parseInt(writerId, 10),
        model_id: modelId,
        title: title || null // Send null if title is empty
    };

    const response = await authenticatedFetch(`/admin/contests/${contestId}/ai-submission`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    const result = await response.json();

    if (!response.ok) {
        let detail = `Error ${response.status}`;
        if (result && result.detail) {
            detail = Array.isArray(result.detail) 
                ? result.detail.map(err => `${err.loc.join(' -> ')}: ${err.msg}`).join('; ') 
                : result.detail;
        }
        throw new Error(`Failed to trigger AI submission: ${detail}`);
    }
    return result;
}

// --- UI Rendering & Logic ---
function populateSelect(selectElement, items, valueField, textField, prompt) {
    if (!selectElement) return;
    selectElement.innerHTML = ''; // Clear previous
    const promptOption = document.createElement('option');
    promptOption.value = '';
    promptOption.textContent = prompt;
    promptOption.disabled = true;
    // promptOption.selected = true; // Don't pre-select the disabled prompt
    selectElement.appendChild(promptOption);

    if (items && items.length > 0) {
         items.forEach(item => {
            const option = document.createElement('option');
            option.value = item[valueField];
            option.textContent = item[textField]; // Adjust if name is complex
            selectElement.appendChild(option);
        });
    } else {
        // Add a disabled option indicating none are available
        const noneOption = document.createElement('option');
        noneOption.value = '';
        noneOption.textContent = `No ${selectElement.id.includes('contest') ? 'concursos abiertos' : 'escritores IA'} disponibles`;
        noneOption.disabled = true;
        selectElement.appendChild(noneOption);
        selectElement.disabled = true; // Disable the select if empty
    }
     selectElement.value = ''; // Ensure the prompt is initially shown
}

async function handleFormSubmit(event) {
    event.preventDefault();
    errorMessageDiv.style.display = 'none';
    successMessageDiv.style.display = 'none';
    if(submitButton) submitButton.disabled = true;
    if(submitButton) submitButton.textContent = 'Generando...';

    const contestId = contestSelect.value;
    const writerId = writerSelect.value;
    const modelId = modelSelect.value;
    const title = titleInput.value.trim();

    if (!contestId || !writerId || !modelId) {
         displayError("Por favor, selecciona un concurso, un escritor IA y un modelo.");
         if(submitButton) submitButton.disabled = false;
         if(submitButton) submitButton.textContent = 'Generar Envío IA';
        return;
    }

    try {
        const result = await triggerAISubmission(contestId, writerId, modelId, title);
        console.log("AI Submission triggered:", result);
        displaySuccess(`Envío generado con éxito para el concurso ${contestId}! (Submission ID: ${result.submission_id}, Título: ${result.title})`);
        // Optionally reset form or parts of it
        // titleInput.value = ''; 
    } catch (error) {
        console.error("AI submission trigger failed:", error);
        displayError(`Error al generar el envío: ${error.message}`);
    } finally {
        if(submitButton) submitButton.disabled = false;
        if(submitButton) submitButton.textContent = 'Generar Envío IA';
    }
}

// --- Page Load Logic ---
document.addEventListener('DOMContentLoaded', async () => {
    // Verify admin role
    if (!isLoggedIn()) {
        window.location.href = `/login.html?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
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
        displayError("Acceso denegado. Se requieren permisos de administrador.");
        if(loadingMessage) loadingMessage.style.display = 'none';
        return;
    }

    // Admin verified, load data for form
    try {
        const [contests, writers] = await Promise.all([
            fetchOpenContests(),
            fetchAIWriters()
        ]);

        populateSelect(contestSelect, contests, 'id', 'title', 'Selecciona un concurso...');
        populateSelect(writerSelect, writers, 'id', 'name', 'Selecciona un escritor IA...');
        // Models are currently hardcoded

        if (loadingMessage) loadingMessage.style.display = 'none';
        if (submissionForm) submissionForm.style.display = 'block';

        // Add form submit listener
        if (submissionForm) {
            submissionForm.addEventListener('submit', handleFormSubmit);
        }

    } catch (error) {
        console.error("Error loading data for AI submission page:", error);
        displayError(`Error al cargar datos: ${error.message}`);
        if(loadingMessage) loadingMessage.style.display = 'none';
    }
}); 