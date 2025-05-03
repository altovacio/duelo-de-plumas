// admin_contest_edit.js - Logic for creating/editing contests

console.log("Admin Contest Edit script loaded.");

// --- DOM Elements ---
const loadingMessage = document.getElementById('loading-message');
const errorMessageDiv = document.getElementById('error-message');
const contestForm = document.getElementById('contest-form');
const pageTitle = document.getElementById('page-title');
const passwordGroup = document.getElementById('password-group');
const contestTypeSelect = document.getElementById('contest_type');
const submitButton = document.getElementById('submit-button');
const aiJudgesListDiv = document.getElementById('ai-judges-list');

// --- State ---
let contestId = null;
let availableAIJudges = []; // Store fetched AI judges

// --- Helper Functions ---
function getContestIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

function displayError(message) {
    if(loadingMessage) loadingMessage.style.display = 'none';
    if(contestForm) contestForm.style.display = 'none';
    if(errorMessageDiv) {
        errorMessageDiv.textContent = message;
        errorMessageDiv.style.display = 'block';
    }
}

// Format date for datetime-local input
function formatDateTimeLocal(isoString) {
    if (!isoString) return '';
    try {
        const date = new Date(isoString);
        // Adjust for timezone offset to get local time in YYYY-MM-DDTHH:mm format
        const offset = date.getTimezoneOffset() * 60000; // Offset in milliseconds
        const localDate = new Date(date.getTime() - offset);
        return localDate.toISOString().slice(0, 16);
    } catch (e) {
        console.error("Error formatting date for input:", isoString, e);
        return '';
    }
}

// --- API Calls ---
async function fetchContestDetails(id) {
    console.log(`Fetching details for contest ${id}`);
    const response = await authenticatedFetch(`/contests/${id}`);
    if (!response.ok) throw new Error(`Failed to fetch contest details: ${response.status}`);
    return response.json();
}

async function fetchAIJudges() {
    console.log("Fetching AI judges...");
    const response = await authenticatedFetch('/admin/ai-judges'); // Using the admin endpoint
    if (!response.ok) throw new Error(`Failed to fetch AI judges: ${response.status}`);
    return response.json();
}

async function saveContest(contestData, isEditing) {
    const url = isEditing ? `/contests/${contestId}` : '/contests/';
    const method = isEditing ? 'PUT' : 'POST';
    console.log(`Saving contest (edit=${isEditing}) to ${url}`);
    
    const response = await authenticatedFetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(contestData)
    });
    
    const result = await response.json(); // Try to parse response regardless of status
    
    if (!response.ok) {
         let detail = `Error ${response.status}`; 
         if(result && result.detail) detail = result.detail;
         // Handle validation errors specifically if backend provides them
         if (response.status === 422 && result.detail) {
             // Format validation errors
             detail = result.detail.map(err => `${err.loc.join(' -> ')}: ${err.msg}`).join('; ');
         }
        throw new Error(`Failed to save contest: ${detail}`);
    }
    return result; // Return created/updated contest data
}

// --- UI Rendering & Logic ---

function populateAIJudges(assignedJudgeIds = []) {
    if (!aiJudgesListDiv) return;
    aiJudgesListDiv.innerHTML = ''; // Clear loading message

    if (availableAIJudges.length === 0) {
        aiJudgesListDiv.innerHTML = '<p>No hay jueces IA configurados.</p>';
        return;
    }

    availableAIJudges.forEach(judge => {
        const isChecked = assignedJudgeIds.includes(judge.id);
        const div = document.createElement('div');
        div.classList.add('form-check'); // Assuming form-check style exists or add it
        div.innerHTML = `
            <input class="form-check-input" type="checkbox" value="${judge.id}" id="judge-${judge.id}" name="judges" ${isChecked ? 'checked' : ''}>
            <label class="form-check-label" for="judge-${judge.id}">
                ${judge.username} (${judge.description || 'Sin descripción'})
            </label>
        `;
        aiJudgesListDiv.appendChild(div);
    });
}

function populateForm(contest) {
    if (!contestForm || !contest) return;
    contestForm.elements['title'].value = contest.title || '';
    contestForm.elements['description'].value = contest.description || '';
    contestForm.elements['status'].value = contest.status || 'draft';
    contestForm.elements['contest_type'].value = contest.contest_type || 'public';
    contestForm.elements['end_date'].value = formatDateTimeLocal(contest.end_date);
    contestForm.elements['required_judges'].value = contest.required_judges || 3;
    
    // Show/hide password based on type
    if (passwordGroup) passwordGroup.style.display = contest.contest_type === 'private' ? 'block' : 'none';
    
    // Populate assigned AI judges
    const assignedIds = contest.judges ? contest.judges.filter(j => j.judge_type === 'ai').map(j => j.id) : [];
    populateAIJudges(assignedIds);
}

async function handleFormSubmit(event) {
    event.preventDefault();
    errorMessageDiv.style.display = 'none';
    errorMessageDiv.textContent = '';
    if(submitButton) submitButton.disabled = true;
    if(submitButton) submitButton.textContent = 'Guardando...';

    const formData = new FormData(contestForm);
    const contestData = {};
    
    // Basic fields
    contestData.title = formData.get('title');
    contestData.description = formData.get('description');
    contestData.status = formData.get('status');
    contestData.contest_type = formData.get('contest_type');
    contestData.required_judges = parseInt(formData.get('required_judges') || '3', 10);
    
    // Optional fields
    const endDate = formData.get('end_date');
    if (endDate) {
        contestData.end_date = new Date(endDate).toISOString(); // Send as ISO string
    }
    const password = formData.get('password');
    if (contestData.contest_type === 'private' && password) {
        contestData.password = password; // Include password only if type is private and field has value
    }
    
    // TODO: Collect assigned judge IDs (AI + Human when available)
    // const assignedJudgeIds = Array.from(formData.getAll('judges')).map(id => parseInt(id, 10));
    // contestData.judge_ids = assignedJudgeIds; // Assuming backend expects judge_ids

    try {
        const result = await saveContest(contestData, contestId !== null);
        console.log("Contest saved:", result);
        // Redirect to admin contests list on success
        window.location.href = '/admin_contests.html';
    } catch (error) {
        console.error("Save contest failed:", error);
        errorMessageDiv.textContent = `Error al guardar: ${error.message}`;
        errorMessageDiv.style.display = 'block';
        if(submitButton) submitButton.disabled = false;
        if(submitButton) submitButton.textContent = contestId ? 'Guardar Cambios' : 'Crear Concurso';
    }
}

// --- Page Load Logic ---
document.addEventListener('DOMContentLoaded', async () => {
    // updateNav called by auth.js
    contestId = getContestIdFromUrl();
    const isEditing = contestId !== null;

    // Verify admin role
    if (!isLoggedIn()) {
        window.location.href = `/login.html?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
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
        displayError("Acceso denegado. Se requieren permisos de administrador.");
        return;
    }

    // Admin verified, proceed
    if(pageTitle) pageTitle.textContent = isEditing ? 'Editar Concurso' : 'Crear Concurso';
    if(submitButton) submitButton.textContent = isEditing ? 'Guardar Cambios' : 'Crear Concurso';
    document.title = `${isEditing ? 'Editar' : 'Crear'} Concurso - Admin`;

    // Show/hide password field based on type selection
    if(contestTypeSelect && passwordGroup) {
        contestTypeSelect.addEventListener('change', (e) => {
            passwordGroup.style.display = e.target.value === 'private' ? 'block' : 'none';
        });
        // Trigger change on load if editing
        if (isEditing) {
             passwordGroup.style.display = contestTypeSelect.value === 'private' ? 'block' : 'none';
        }
    }

    // Fetch AI judges first
    try {
        availableAIJudges = await fetchAIJudges();
        // Populate judges list (initially with no selections for create mode)
        populateAIJudges([]); 
    } catch (error) {
        console.error("Failed to load AI judges list:", error);
        if(aiJudgesListDiv) aiJudgesListDiv.innerHTML = '<p style="color: red;">Error al cargar jueces IA.</p>';
    }
    
    // If editing, fetch contest details and populate form
    if (isEditing) {
        try {
            const contest = await fetchContestDetails(contestId);
            populateForm(contest);
            if(loadingMessage) loadingMessage.style.display = 'none';
            if(contestForm) contestForm.style.display = 'block';
        } catch (error) {
            console.error("Error loading contest details:", error);
            displayError(`Error al cargar datos del concurso: ${error.message}`);
        }
    } else {
        // Create mode: just show the form after judges loaded (or tried to load)
        if(loadingMessage) loadingMessage.style.display = 'none';
        if(contestForm) contestForm.style.display = 'block';
        populateAIJudges([]); // Ensure it's populated even if fetch failed earlier
    }

    // Add form submit listener
    if (contestForm) {
        contestForm.addEventListener('submit', handleFormSubmit);
    }
}); 