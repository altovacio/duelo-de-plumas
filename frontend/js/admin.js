// admin.js - Logic for the main admin dashboard

console.log("Admin dashboard script loaded.");

const loadingMessage = document.getElementById('loading-message');
const errorMessageDiv = document.getElementById('error-message');
const adminContentDiv = document.getElementById('admin-content');

function showAdminContent() {
    if(loadingMessage) loadingMessage.style.display = 'none';
    if(errorMessageDiv) errorMessageDiv.style.display = 'none';
    if(adminContentDiv) adminContentDiv.style.display = 'block';
}

function displayAdminError(message) {
    if(loadingMessage) loadingMessage.style.display = 'none';
    if(adminContentDiv) adminContentDiv.style.display = 'none';
    if(errorMessageDiv) {
        errorMessageDiv.textContent = message;
        errorMessageDiv.style.display = 'block';
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    // updateNav will be called from auth.js, which should now handle showing the admin link
    // We still need to verify the user *role* here before showing content
    
    if (!isLoggedIn()) {
        // Should not happen if routing/nav is correct, but as a fallback
        window.location.href = `/login.html?next=${encodeURIComponent(window.location.pathname)}`;
        return;
    }
    
    // Fetch user details to verify role
    try {
        const response = await authenticatedFetch('/auth/users/me');
        
        if (response.ok) {
            const user = await response.json();
            console.log("Current user:", user);
            if (user && user.role === 'admin') {
                // User is admin, show the content
                showAdminContent();
                 // TODO: Optionally fetch dashboard data here if needed for admin panel
            } else {
                // User is logged in but not admin
                displayAdminError("Acceso denegado. Se requieren permisos de administrador.");
                // Hide admin link in nav if somehow visible (should be handled by updateNav)
                const adminLink = document.getElementById('nav-admin');
                if(adminLink) adminLink.style.display = 'none'; 
            }
        } else {
            // Error fetching user details (e.g., token expired, server error)
            console.error("Error fetching user details:", response.status);
             displayAdminError(`Error ${response.status}: No se pudo verificar el estado del usuario. Intenta iniciar sesión de nuevo.`);
             // Consider redirecting to login if 401
             if (response.status === 401) {
                 // Maybe logout completely?
                 // logout(); 
             }
        }
    } catch (error) {
        console.error("Network or other error fetching user details:", error);
        displayAdminError("Error de red al verificar el estado del usuario.");
    }
}); 