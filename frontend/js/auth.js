// auth.js - Shared authentication utilities

console.log("Auth utils loaded.");

const TOKEN_KEY = 'accessToken';

// Stored user info to avoid multiple fetches per navigation
let currentUserInfo = null;
let userInfoPromise = null;

/**
 * Checks if a user access token exists in local storage.
 * @returns {boolean} True if the token exists, false otherwise.
 */
function isLoggedIn() {
    return localStorage.getItem(TOKEN_KEY) !== null;
}

/**
 * Retrieves the access token from local storage.
 * @returns {string|null} The access token or null if not found.
 */
function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

/**
 * Removes the access token from local storage and redirects to home.
 */
function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem('tokenType'); // Remove token type as well
    currentUserInfo = null; // Clear user info cache
    console.log("User logged out.");
    window.location.href = '/'; // Redirect to home page after logout
}

/** Fetches user info if needed, otherwise returns cached */
async function getUserInfo() {
    if (currentUserInfo) return currentUserInfo;
    if (!isLoggedIn()) return null;

    // If a fetch is already in progress, wait for it
    if (userInfoPromise) {
        try {
            return await userInfoPromise;
        } catch (e) {
            return null; // Return null if the ongoing fetch fails
        }
    }

    // Start a new fetch
    userInfoPromise = (async () => {
        try {
            console.log("Fetching user info for nav...");
            const response = await authenticatedFetch('/auth/users/me');
            if (response.ok) {
                currentUserInfo = await response.json();
                return currentUserInfo;
            } else {
                console.warn(`Failed to fetch user info: ${response.status}`);
                // If fetch fails (e.g., 401), clear stored token?
                // localStorage.removeItem(TOKEN_KEY);
                currentUserInfo = null; // Ensure cache is cleared on failure
                return null;
            }
        } catch (error) {
            console.error("Error fetching user info:", error);
            currentUserInfo = null; // Ensure cache is cleared on failure
            throw error; // Re-throw so the caller knows it failed
        } finally {
            userInfoPromise = null; // Allow future fetches
        }
    })();

    try {
        return await userInfoPromise;
    } catch (e) {
        return null; // Return null if the fetch fails
    }
}

/**
 * Updates the navigation links based on login status and user role.
 */
async function updateNav() {
    const loginLink = document.getElementById('nav-login');
    const logoutLinkLi = document.getElementById('nav-logout-li');
    const adminLinkLi = document.getElementById('nav-admin'); // Expecting the li element

    const user = await getUserInfo(); // Fetch or get cached user info

    if (user) {
        // Logged In
        if (loginLink) loginLink.style.display = 'none';
        if (logoutLinkLi) logoutLinkLi.style.display = ''; 
        
        // Show Admin link only if user role is admin
        if (adminLinkLi) {
            if (user.role === 'admin') {
                adminLinkLi.style.display = '';
            } else {
                adminLinkLi.style.display = 'none';
            }
        }
    } else {
        // Logged Out
        if (loginLink) loginLink.style.display = '';
        if (logoutLinkLi) logoutLinkLi.style.display = 'none'; 
        if (adminLinkLi) adminLinkLi.style.display = 'none'; 
        currentUserInfo = null; // Clear cache on logout detection
    }
    
    // Add event listener for logout button
    const logoutButton = document.getElementById('nav-logout-button');
    if (logoutButton && logoutLinkLi && logoutLinkLi.style.display !== 'none') {
        if (!logoutButton.dataset.listenerAttached) {
             logoutButton.addEventListener('click', (e) => {
                 e.preventDefault();
                 currentUserInfo = null; // Clear cache before logging out
                 logout();
             });
             logoutButton.dataset.listenerAttached = 'true';
        }
    }
}

/**
 * Performs a fetch request, adding the Authorization header if a token exists.
 * @param {string} url The URL to fetch.
 * @param {object} options Fetch options (method, body, headers, etc.).
 * @returns {Promise<Response>} The fetch response.
 */
async function authenticatedFetch(url, options = {}) {
    const token = getToken();
    const headers = { ...options.headers };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const fetchOptions = {
        ...options,
        headers,
    };

    // Check for 401 Unauthorized response and potentially clear token/redirect
    const response = await fetch(url, fetchOptions);
    if (response.status === 401 && url !== '/auth/token') { // Don't clear on login failure
        console.warn('Received 401 Unauthorized. Clearing token and potentially redirecting.');
        // Maybe redirect only if not already on login page?
        // if (window.location.pathname !== '/login.html') {
        //     logout(); // This will clear token and redirect
        // }
    }
    return response;
}

// Call updateNav automatically when auth.js loads
document.addEventListener('DOMContentLoaded', updateNav); 