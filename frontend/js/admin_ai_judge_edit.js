// admin_ai_judge_edit.js - Logic for creating/editing AI judges

console.log("Admin AI Judge Edit script loaded.");

// --- DOM Elements ---
const loadingMessage = document.getElementById('loading-message');
const errorMessageDiv = document.getElementById('error-message');
const judgeForm = document.getElementById('ai-judge-form');
const pageTitle = document.getElementById('page-title');
const submitButton = document.getElementById('submit-button');
const nameInput = document.getElementById('name');

// --- State ---
let judgeId = null;

// --- Helper Functions ---
function getJudgeIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

function displayError(message) {
    if(loadingMessage) loadingMessage.style.display = 'none';
    if(judgeForm) judgeForm.style.display = 'none';
    if(errorMessageDiv) {
        errorMessageDiv.textContent = message;
        errorMessageDiv.style.display = 'block';
    }
}

// --- API Calls ---
async function fetchAIJudgeDetails(id) {
    console.log(`Fetching details for AI judge ${id}`);
    const response = await authenticatedFetch(`/admin/ai-judges/${id}`);
    if (!response.ok) throw new Error(`Failed to fetch AI judge details: ${response.status}`);
    return response.json();
}

async function saveAIJudge(judgeData, isEditing) {
    const url = isEditing ? `/admin/ai-judges/${judgeId}` : '/admin/ai-judges';
    const method = isEditing ? 'PUT' : 'POST';
    console.log(`Saving AI judge (edit=${isEditing}) to ${url} with data:`, judgeData);
    
    const payload = isEditing ? { 
        name: judgeData.name,
        description: judgeData.description,
        ai_personality_prompt: judgeData.ai_personality_prompt,
    } : judgeData;

    const response = await authenticatedFetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    
    if (!response.ok) {
         let detail = `Error ${response.status}`; 
         if(result && result.detail) detail = result.detail;
         if (response.status === 422 && result.detail) {
             detail = result.detail.map(err => `${err.loc.join(' -> ')}: ${err.msg}`).join('; ');
         }
        throw new Error(`Failed to save AI judge: ${detail}`);
    }
    return result; 
}

// --- UI Rendering & Logic ---
function populateForm(judge) {
    if (!judgeForm || !judge) return;
    judgeForm.elements['name'].value = judge.name || '';
    judgeForm.elements['description'].value = judge.description || '';
    judgeForm.elements['ai_personality_prompt'].value = judge.ai_personality_prompt || '';
    
    if (nameInput) nameInput.readOnly = true; 
}

async function handleFormSubmit(event) {
    event.preventDefault();
    errorMessageDiv.style.display = 'none';
    errorMessageDiv.textContent = '';

    const isEditing = judgeId !== null;
    const formData = new FormData(judgeForm);

    if(submitButton) submitButton.disabled = true;
    if(submitButton) submitButton.textContent = 'Guardando...';

    const judgeData = {
        name: formData.get('name'),
        description: formData.get('description') || null,
        ai_personality_prompt: formData.get('ai_personality_prompt')
    };

    try {
        const result = await saveAIJudge(judgeData, isEditing);
        console.log("AI Judge saved:", result);
        window.location.href = '/admin_ai_judges.html';
    } catch (error) {
        console.error("Save AI judge failed:", error);
        errorMessageDiv.textContent = `Error al guardar: ${error.message}`;
        errorMessageDiv.style.display = 'block';
        if(submitButton) submitButton.disabled = false;
        if(submitButton) submitButton.textContent = isEditing ? 'Guardar Cambios en Perfil' : 'Crear Perfil de Juez IA';
    }
}

// --- Page Load Logic ---
document.addEventListener('DOMContentLoaded', async () => {
    judgeId = getJudgeIdFromUrl();
    const isEditing = judgeId !== null;

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
        return;
    }

    // Admin verified, proceed
    if(pageTitle) pageTitle.textContent = isEditing ? 'Editar Perfil de Juez IA' : 'Crear Perfil de Juez IA';
    if(submitButton) submitButton.textContent = isEditing ? 'Guardar Cambios en Perfil' : 'Crear Perfil de Juez IA';
    document.title = `${isEditing ? 'Editar' : 'Crear'} Perfil de Juez IA - Admin`;

    if (isEditing) {
        // Edit mode: Fetch details
        try {
            const judge = await fetchAIJudgeDetails(judgeId);
            populateForm(judge);
            if(loadingMessage) loadingMessage.style.display = 'none';
            if(judgeForm) judgeForm.style.display = 'block';
        } catch (error) {
            console.error("Error loading AI judge details:", error);
            displayError(`Error al cargar datos del juez IA: ${error.message}`);
        }
    } else {
        // Create mode: Just show the form
        if(loadingMessage) loadingMessage.style.display = 'none';
        if(judgeForm) judgeForm.style.display = 'block';
        if (nameInput) nameInput.readOnly = false;
    }

    // Add form submit listener
    if (judgeForm) {
        judgeForm.addEventListener('submit', handleFormSubmit);
    }
}); 