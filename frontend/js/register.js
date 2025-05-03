// register.js - Logic for the registration page

console.log("Register page script loaded.");

document.addEventListener('DOMContentLoaded', () => {
    updateNav(); // Ensure nav is correct

    const registerForm = document.getElementById('register-form');
    const errorMessageDiv = document.getElementById('error-message');
    const successMessageDiv = document.getElementById('success-message');

    if (registerForm) {
        registerForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            errorMessageDiv.style.display = 'none';
            successMessageDiv.style.display = 'none';
            errorMessageDiv.textContent = '';
            successMessageDiv.textContent = '';

            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm-password').value;

            // Basic client-side validation
            if (password !== confirmPassword) {
                errorMessageDiv.textContent = 'Las contraseñas no coinciden.';
                errorMessageDiv.style.display = 'block';
                return;
            }
            if (password.length < 8) { // Example: Minimum password length
                errorMessageDiv.textContent = 'La contraseña debe tener al menos 8 caracteres.';
                errorMessageDiv.style.display = 'block';
                return;
            }

            const userData = {
                username: username,
                email: email,
                password: password
                // Role is determined by backend logic (defaults to 'judge' likely)
            };

            try {
                console.log("Attempting registration...");
                const response = await fetch('/auth/register', { 
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(userData),
                });

                const result = await response.json();

                if (!response.ok) {
                    let errorDetail = "Error desconocido al registrar.";
                    if (result && result.detail) {
                        errorDetail = result.detail;
                    }
                    console.error("Registration failed:", response.status, result);
                    errorMessageDiv.textContent = errorDetail;
                    errorMessageDiv.style.display = 'block';
                } else {
                    // Registration successful
                    console.log("Registration successful:", result);
                    successMessageDiv.textContent = '¡Registro exitoso! Ahora puedes iniciar sesión.';
                    successMessageDiv.style.display = 'block';
                    registerForm.reset(); // Clear the form
                    
                    // Optional: Redirect to login after a short delay
                    // setTimeout(() => {
                    //     window.location.href = '/login.html';
                    // }, 3000); 
                }

            } catch (error) {
                console.error("Network or other error during registration:", error);
                errorMessageDiv.textContent = "Error de red o al contactar el servidor.";
                errorMessageDiv.style.display = 'block';
            }
        });
    }
}); 