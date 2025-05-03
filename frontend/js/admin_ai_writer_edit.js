// admin_ai_writer_edit.js - Logic for creating/editing AI writers

console.log("Admin AI Writer Edit script loaded.");

// --- DOM Elements ---
const loadingMessage = document.getElementById('loading-message');
const errorMessageDiv = document.getElementById('error-message');
const writerForm = document.getElementById('ai-writer-form');
const pageTitle = document.getElementById('page-title');
const submitButton = document.getElementById('submit-button');
const nameInput = document.getElementById('name');

// --- State ---
let writerId = null;

// --- Helper Functions ---
function getWriterIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

function displayError(message) {
    if(loadingMessage) loadingMessage.style.display = 'none';
    if(writerForm) writerForm.style.display = 'none';
    if(errorMessageDiv) {
        errorMessageDiv.textContent = message;
        errorMessageDiv.style.display = 'block';
    }
}

// --- API Calls ---
async function fetchAIWriterDetails(id) {
    console.log(`Fetching details for AI writer ${id}`);
    const response = await authenticatedFetch(`/admin/ai-writers/${id}`);
    if (!response.ok) throw new Error(`Failed to fetch AI writer details: ${response.status}`);
    return response.json();
}

async function saveAIWriter(writerData, isEditing) {
    const url = isEditing ? `/admin/ai-writers/${writerId}` : '/admin/ai-writers'; // No trailing slash for POST
    const method = isEditing ? 'PUT' : 'POST';
    console.log(`Saving AI writer (edit=${isEditing}) to ${url} with data:`, writerData);
    
    // AIWriterCreate needs name, description?, personality_prompt
    // AIWriterUpdate needs description?, personality_prompt? (Name is usually not updatable via PUT)
    const payload = isEditing ? {
         description: writerData.description, 
         personality_prompt: writerData.personality_prompt
     } : {
        name: writerData.name,
        description: writerData.description,
        personality_prompt: writerData.personality_prompt
     }; // Send full data for POST

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
        throw new Error(`Failed to save AI writer: ${detail}`);
    }
    return result; 
}

// --- UI Rendering & Logic ---
function populateForm(writer) {
    if (!writerForm || !writer) return;
    writerForm.elements['name'].value = writer.name || '';
    writerForm.elements['description'].value = writer.description || '';
    writerForm.elements['personality_prompt'].value = writer.personality_prompt || '';
    
    // Make name read-only in edit mode?
    if (nameInput) nameInput.readOnly = true; 
}

async function handleFormSubmit(event) {
    event.preventDefault();
    errorMessageDiv.style.display = 'none';
    errorMessageDiv.textContent = '';
    if(submitButton) submitButton.disabled = true;
    if(submitButton) submitButton.textContent = 'Guardando...';

    const formData = new FormData(writerForm);
    const writerData = {
        name: formData.get('name'), // Required for create
        description: formData.get('description') || null,
        personality_prompt: formData.get('personality_prompt') || null
    };
    
    // Removed previous complex payload logic, handled in saveAIWriter now

    try {
        // Pass the correct isEditing flag
        const result = await saveAIWriter(writerData, writerId !== null);
        console.log("AI Writer saved:", result);
        window.location.href = '/admin_ai_writers.html';
        if(submitButton) submitButton.disabled = false;
        if(submitButton) submitButton.textContent = writerId ? 'Guardar Cambios en Perfil' : 'Crear Perfil de Escritor IA'; // Use consistent text
    } catch (error) {
        console.error("Save AI writer failed:", error);
        errorMessageDiv.textContent = `Error al guardar: ${error.message}`;
        errorMessageDiv.style.display = 'block';
        if(submitButton) submitButton.disabled = false;
        if(submitButton) submitButton.textContent = writerId ? 'Guardar Cambios en Perfil' : 'Crear Perfil de Escritor IA'; // Use consistent text
    }
}

// --- Page Load Logic ---
document.addEventListener('DOMContentLoaded', async () => {
    console.log("DOM content loaded for AI writer edit.");
    // Check auth and admin status first
    if (!isLoggedIn()) {
        window.location.href = `/login.html?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
        return;
    }
    let isAdmin = false;
    try {
        const user = await getUserInfo(); // Use cached info if available
        if (user && user.role === 'admin') {
            isAdmin = true;
        } 
    } catch (error) {
        console.warn("Error checking user info:", error);
    }

    if (!isAdmin) {
        displayError("Acceso denegado. Se requieren permisos de administrador.");
        return;
    }

    // Determine if editing or creating
    writerId = getWriterIdFromUrl();
    const isEditing = writerId !== null;
    console.log(`Mode: ${isEditing ? 'Editing' : 'Creating'} AI Writer (ID: ${writerId})`);

    if (pageTitle) pageTitle.textContent = isEditing ? 'Editar Perfil de Escritor IA' : 'Crear Nuevo Perfil de Escritor IA';
    if (submitButton) submitButton.textContent = isEditing ? 'Guardar Cambios en Perfil' : 'Crear Perfil de Escritor IA';

    // Attach form submit listener
    if (writerForm) {
        writerForm.addEventListener('submit', handleFormSubmit);
    } else {
        console.error("Writer form not found!");
        displayError("Error crítico: No se encontró el formulario.");
        return;
    }

    if (isEditing) {
        // Edit mode: Fetch existing data
        try {
            const writer = await fetchAIWriterDetails(writerId);
            populateForm(writer);
            if (loadingMessage) loadingMessage.style.display = 'none';
            if (writerForm) writerForm.style.display = 'block';
        } catch (error) {
            console.error("Error loading writer details:", error);
            displayError(`Error al cargar datos del escritor: ${error.message}`);
        }
    } else {
        // Create mode: No data to fetch, just show the form
        if (nameInput) nameInput.readOnly = false; // Ensure name is editable
        if (loadingMessage) loadingMessage.style.display = 'none';
        if (writerForm) writerForm.style.display = 'block';
        console.log("Create mode: Form displayed.");
    }
});