// Basic script
console.log("Frontend script loaded.");

// --- Helper Functions ---

// Function to format dates (simple example)
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        // Attempt to parse directly, assuming ISO 8601 format from FastAPI
        return new Date(dateString).toLocaleDateString(undefined, options);
    } catch (e) {
        console.error("Error formatting date:", dateString, e);
        return dateString; // Return original string on error
    }
}

// --- API Fetching ---

// Use the authenticatedFetch wrapper from auth.js
// No longer need the local fetchData function
/* 
async function fetchData(endpoint) { ... } 
*/

// --- UI Rendering ---

// Function to create a contest list item element
function createContestElement(contest) {
    const listItem = document.createElement('li');
    listItem.classList.add('contest-item');
    
    // Basic structure - adapt based on actual contest object properties
    listItem.innerHTML = `
        <h3 class="contest-title">
            <a href="/contest.html?id=${contest.id}">${contest.title}</a> 
            ${contest.contest_type === 'private' ? '<span class="private-badge">(Privado)</span>' : ''}
        </h3>
        <p class="contest-description">${contest.description || ''}</p>
        <div class="contest-meta">
            <span>Estado: ${contest.status}</span> 
            ${contest.end_date ? `<span> | Fecha Límite: ${formatDate(contest.end_date)}</span>` : ''}
            <!-- Add more meta info later: submissions count, etc. -->
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
    
    listElement.innerHTML = ''; // Clear previous items
    
    if (contests && contests.length > 0) {
        contests.forEach(contest => {
            const contestElement = createContestElement(contest);
            listElement.appendChild(contestElement);
        });
        messageElement.style.display = 'none';
        listElement.style.display = ''; // Or 'grid' if needed
    } else {
        messageElement.style.display = 'block';
        listElement.style.display = 'none';
    }
}

// --- Page Load Logic ---

document.addEventListener('DOMContentLoaded', async () => {
    console.log("DOM fully loaded and parsed");
    updateNav(); // Update nav based on login status
    
    // Use authenticatedFetch to get dashboard data
    const response = await authenticatedFetch('/api/v2/dashboard-data');
    let dashboardData = null;
    
    if (response.ok) {
        try {
            dashboardData = await response.json();
        } catch (e) {
            console.error("Error parsing dashboard data JSON:", e);
        }
    } else {
        // Handle non-OK responses (like 401 if token is invalid/expired, or other errors)
        console.warn(`Failed to fetch dashboard data: ${response.status}`);
        // If 401, maybe redirect to login or just show public view?
        // For now, we just won't have the data.
    }
    
    if (dashboardData) {
        // Display public contest lists
        displayContestList('active-contests', dashboardData.active_contests);
        displayContestList('closed-contests', dashboardData.closed_contests);
        
        // Handle conditional sections (Judge/Admin)
        const judgeQueueSection = document.getElementById('judge-queue');
        if (dashboardData.judge_assigned_evaluations && dashboardData.judge_assigned_evaluations.length > 0 && judgeQueueSection) {
            displayContestList('judge-queue', dashboardData.judge_assigned_evaluations);
            judgeQueueSection.style.display = 'block';
        }
        
        const adminAlertsSection = document.getElementById('admin-alerts');
        const expiredContests = dashboardData.expired_open_contests;
        const pendingAiEvals = dashboardData.pending_ai_evaluations;
        
        let showAdminAlerts = false;
        if (expiredContests && expiredContests.length > 0) {
             displayContestList('expired-open-contests', expiredContests);
             showAdminAlerts = true;
        }
        if (pendingAiEvals && pendingAiEvals.length > 0) {
            displayContestList('pending-ai-evaluations', pendingAiEvals);
            showAdminAlerts = true;
        }
        
        if (showAdminAlerts && adminAlertsSection) {
            adminAlertsSection.style.display = 'block';
        }
        
    } else {
        console.warn("Displaying dashboard with potentially missing data.");
        // Show empty state for all sections if data fetch failed
        displayContestList('active-contests', []);
        displayContestList('closed-contests', []);
        displayContestList('judge-queue', []); // Ensure judge queue is cleared
        displayContestList('expired-open-contests', []); // Ensure admin alerts are cleared
        displayContestList('pending-ai-evaluations', []);
        // Hide conditional sections if no data
        const judgeQueueSection = document.getElementById('judge-queue');
        if (judgeQueueSection) judgeQueueSection.style.display = 'none';
        const adminAlertsSection = document.getElementById('admin-alerts');
        if (adminAlertsSection) adminAlertsSection.style.display = 'none';
    }
});

// Remove old roadmap display function
/*
function displayRoadmap(items) {
    const listElement = document.getElementById('roadmap-list');
    if (!listElement) {
        console.error("Element with id 'roadmap-list' not found.");
        return;
    }
    listElement.innerHTML = ''; // Clear existing items

    if (!items || items.length === 0) {
        listElement.innerHTML = '<li>No roadmap items found.</li>';
        return;
    }

    items.forEach(item => {
        const listItem = document.createElement('li');
        listItem.textContent = `[${item.status}] ${item.text} (ID: ${item.id})`;
        listElement.appendChild(listItem);
    });
}
*/ 