// contest.js - Logic for the contest detail page

console.log("Contest detail page script loaded.");

// --- Helper Functions (Copied from script.js / contests.js) ---
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        return new Date(dateString).toLocaleDateString(undefined, options);
    } catch (e) {
        console.error("Error formatting date:", dateString, e);
        return dateString;
    }
}

// --- DOM Elements ---
const loadingMessage = document.getElementById('loading-message');
const errorMessageDiv = document.getElementById('error-message');
const contestContentDiv = document.getElementById('contest-content');
const contestTitleH1 = document.getElementById('contest-title');
const contestMetaDiv = document.getElementById('contest-meta');
const contestDescriptionP = document.getElementById('contest-description');
const submissionSection = document.getElementById('submission-section');
const resultsSection = document.getElementById('results-section');
const resultsTableBody = document.querySelector('#results-table tbody');
const noResultsMessage = document.getElementById('no-results-message');

// --- Functions ---

function displayError(message) {
    if (loadingMessage) loadingMessage.style.display = 'none';
    if (contestContentDiv) contestContentDiv.style.display = 'none';
    if (errorMessageDiv) {
        errorMessageDiv.textContent = message;
        errorMessageDiv.style.display = 'block';
    }
}

function displayContestDetails(contest) {
    if (!contest) {
        displayError("No se recibieron datos del concurso.");
        return;
    }

    document.title = `${contest.title} - Duelo de Plumas`; // Update page title
    if (contestTitleH1) contestTitleH1.textContent = contest.title;
    if (contestDescriptionP) contestDescriptionP.textContent = contest.description;
    
    // Populate Meta
    if (contestMetaDiv) {
        contestMetaDiv.innerHTML = `
            <span>Estado: ${contest.status}</span>
            ${contest.start_date ? `<span> | Inicio: ${formatDate(contest.start_date)}</span>` : ''}
            ${contest.end_date ? `<span> | Fin: ${formatDate(contest.end_date)}</span>` : ''}
            ${contest.contest_type === 'private' ? '<span class="private-badge"> | (Privado)</span>' : ''}
        `;
    }

    // Handle sections based on status
    if (contest.status === 'open') {
        // Check end date
        const isExpired = contest.end_date && new Date(contest.end_date) < new Date();
        if (!isExpired && submissionSection) {
            submissionSection.style.display = 'block';
        } else {
            // Maybe show a message that it's expired? Or just hide form.
        }
    } else if (contest.status === 'closed') {
        if (resultsSection) resultsSection.style.display = 'block';
        displayResults(contest.submissions || []); // Display results
    } else if (contest.status === 'evaluation') {
         // Maybe show a message that evaluation is in progress?
         if (resultsSection) {
             resultsSection.style.display = 'block'; // Show section
             if(noResultsMessage) noResultsMessage.textContent = "El concurso está en evaluación.";
             if(noResultsMessage) noResultsMessage.style.display = 'block'; // Show message
             if(document.getElementById('results-table')) document.getElementById('results-table').style.display = 'none'; // Hide table
         }
    }

    // Show content, hide loading
    if (loadingMessage) loadingMessage.style.display = 'none';
    if (contestContentDiv) contestContentDiv.style.display = 'block';
}

function displayResults(submissions) {
    if (!resultsTableBody) return;
    resultsTableBody.innerHTML = ''; // Clear previous results
    
    if (!submissions || submissions.length === 0) {
        if (noResultsMessage) noResultsMessage.style.display = 'block';
        if (document.getElementById('results-table')) document.getElementById('results-table').style.display = 'none';
        return;
    } else {
        if (noResultsMessage) noResultsMessage.style.display = 'none';
         if (document.getElementById('results-table')) document.getElementById('results-table').style.display = '';
    }

    // Sort submissions by rank, then points (assuming these fields exist)
    submissions.sort((a, b) => {
        const rankA = a.final_rank ?? Infinity;
        const rankB = b.final_rank ?? Infinity;
        if (rankA !== rankB) {
            return rankA - rankB;
        }
        // If ranks are equal or null, sort by points descending
        const pointsA = a.total_points ?? -Infinity;
        const pointsB = b.total_points ?? -Infinity;
        return pointsB - pointsA;
    });

    submissions.forEach(sub => {
        const row = resultsTableBody.insertRow();
        row.innerHTML = `
            <td>${sub.final_rank ?? 'N/A'}</td>
            <td>${sub.title}</td>
            <td>${sub.author_name}</td>
            <td>${sub.total_points ?? '-'}</td> 
        `;
    });
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
    // Use authenticatedFetch as access might be required for private contests
    const response = await authenticatedFetch(`/contests/${contestId}`);

    if (response.ok) {
        try {
            const contestData = await response.json();
            console.log("Contest data fetched:", contestData);
            displayContestDetails(contestData);
        } catch (e) {
            console.error("Error parsing contest data JSON:", e);
            displayError("Error al procesar los datos del concurso.");
        }
    } else {
        let errorMsg = `Error ${response.status}: Error desconocido al cargar el concurso.`;
        if (response.status === 404) {
            errorMsg = "Error 404: Concurso no encontrado.";
        } else if (response.status === 403) {
            errorMsg = "Error 403: Acceso denegado a este concurso privado.";
        } else if (response.status === 401) {
             errorMsg = "Error 401: Necesitas iniciar sesión para ver este concurso.";
             // Optionally redirect to login: window.location.href = `/login.html?next=/contest.html?id=${contestId}`;
        }
        try {
             // Try to get detail message from backend
             const errorResult = await response.json();
             if (errorResult && errorResult.detail) {
                 errorMsg += ` (${errorResult.detail})`;
             }
        } catch(e) { /* Ignore if error response is not JSON */ }
        
        displayError(errorMsg);
    }
}); 