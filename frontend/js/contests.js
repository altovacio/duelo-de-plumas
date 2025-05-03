// contests.js - Logic for the contests list page

console.log("Contests page script loaded.");

// --- Helper Functions (Copied from script.js) ---

// Function to format dates (simple example)
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

// --- API Fetching (Copied from script.js) ---

// Use the authenticatedFetch wrapper from auth.js
/*
async function fetchData(endpoint) {
    // ... implementation removed ...
}
*/

// --- UI Rendering (Copied and adapted from script.js) ---

// Function to create a contest list item element
function createContestElement(contest) {
    const listItem = document.createElement('li');
    listItem.classList.add('contest-item');
    listItem.innerHTML = `
        <h3 class="contest-title">
             <a href="/contest.html?id=${contest.id}">${contest.title}</a> 
             ${contest.contest_type === 'private' ? '<span class="private-badge">(Privado)</span>' : ''}
         </h3>
        <p class="contest-description">${contest.description || ''}</p>
        <div class="contest-meta">
             <span>Estado: ${contest.status}</span> 
             ${contest.end_date ? `<span> | Fecha Límite: ${formatDate(contest.end_date)}</span>` : ''}
         </div>
    `;
    return listItem;
}

// Function to display a list of contests in a given container
function displayContestList(containerId, contests) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container element with id '${containerId}' not found.`);
        return;
    }
    const listElement = container.querySelector('.contest-list');
    const messageElement = container.querySelector('.no-contests-message');
    if (!listElement || !messageElement) {
        console.error(`Required elements (.contest-list or .no-contests-message) not found within #${containerId}.`);
        return;
    }
    listElement.innerHTML = '';
    if (contests && contests.length > 0) {
        contests.forEach(contest => {
            const contestElement = createContestElement(contest);
            listElement.appendChild(contestElement);
        });
        messageElement.style.display = 'none';
        listElement.style.display = ''; // Or 'grid'
    } else {
        messageElement.style.display = 'block';
        listElement.style.display = 'none';
    }
}

// --- Page Load Logic ---

document.addEventListener('DOMContentLoaded', async () => {
    console.log("Contests page DOM fully loaded and parsed");
    updateNav(); // Update nav based on login status

    // Use authenticatedFetch for dashboard data
    const response = await authenticatedFetch('/api/v2/dashboard-data');
    let dashboardData = null;

    if (response.ok) {
        try {
            dashboardData = await response.json();
        } catch (e) {
            console.error("Error parsing dashboard data JSON:", e);
        }
    } else {
        console.warn(`Failed to fetch dashboard data for contests page: ${response.status}`);
    }

    if (dashboardData) {
        // Display contest lists by status
        const now = new Date(); 
        const openContests = dashboardData.active_contests 
            ? dashboardData.active_contests.filter(c => !c.end_date || new Date(c.end_date) > now) 
            : [];
        const expiredOpenContests = dashboardData.active_contests 
            ? dashboardData.active_contests.filter(c => c.end_date && new Date(c.end_date) <= now) 
            : [];

        displayContestList('open-contests', openContests);
        displayContestList('expired-open-contests', expiredOpenContests); 
        displayContestList('closed-contests', dashboardData.closed_contests);

    } else {
        console.error("Displaying contests page with missing data.");
        displayContestList('open-contests', []);
        displayContestList('expired-open-contests', []);
        displayContestList('closed-contests', []);
    }
}); 