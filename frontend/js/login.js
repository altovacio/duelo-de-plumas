// login.js - Logic for the login page

console.log("Login page script loaded.");

document.addEventListener('DOMContentLoaded', () => {
    updateNav(); // Ensure nav is correct even on login page

    const loginForm = document.getElementById('login-form');
    const errorMessageDiv = document.getElementById('error-message');

    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // Prevent default HTML form submission
            errorMessageDiv.style.display = 'none'; // Hide previous errors
            errorMessageDiv.textContent = '';

            const formData = new FormData(loginForm);
            // Note: FormData automatically uses 'application/x-www-form-urlencoded' 
            // when used with fetch, which matches FastAPI's OAuth2PasswordRequestForm

            try {
                console.log("Attempting login...");
                // The login endpoint is /auth/token relative to backend host
                const response = await fetch('/auth/token', { 
                    method: 'POST',
                    body: formData,
                    // No 'Content-Type' header needed for FormData, browser sets it
                });

                const result = await response.json(); // Try to parse JSON regardless of status

                if (!response.ok) {
                    // Handle errors (e.g., 401 Unauthorized)
                    let errorDetail = "Error desconocido al iniciar sesión.";
                    if (result && result.detail) {
                         errorDetail = result.detail;
                    }
                    console.error("Login failed:", response.status, result);
                    errorMessageDiv.textContent = errorDetail;
                    errorMessageDiv.style.display = 'block';
                } else {
                    // Login successful
                    console.log("Login successful:", result);
                    // Store the token (e.g., in localStorage)
                    // IMPORTANT: localStorage is simple but has security implications (XSS).
                    // For production, consider httpOnly cookies managed by the backend 
                    // or more secure storage mechanisms.
                    if (result.access_token) {
                        localStorage.setItem('accessToken', result.access_token);
                        localStorage.setItem('tokenType', result.token_type);
                        
                        // Redirect to the main page or intended page
                        window.location.href = '/'; 
                    } else {
                         errorMessageDiv.textContent = "Respuesta de inicio de sesión inválida del servidor.";
                         errorMessageDiv.style.display = 'block';
                    }
                }

            } catch (error) {
                console.error("Network or other error during login:", error);
                errorMessageDiv.textContent = "Error de red o al contactar el servidor.";
                errorMessageDiv.style.display = 'block';
            }
        });
    }
}); 