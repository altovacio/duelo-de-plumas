// Placeholder for future JavaScript enhancements
console.log("Duelo de Plumas script loaded.");

// Form validation and UI enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Password visibility toggle (except in edit_contest.html which has its own implementation)
    const isEditContestPage = document.querySelector('#password-field .password-toggle') !== null;
    
    if (!isEditContestPage) {
        const passwordToggles = document.querySelectorAll('.password-toggle');
        passwordToggles.forEach(toggle => {
            toggle.addEventListener('click', function() {
                // Find the password field - either the previous sibling or inside the same container
                let passwordField;
                
                if (this.previousElementSibling && this.previousElementSibling.type === 'password') {
                    // Direct previous sibling
                    passwordField = this.previousElementSibling;
                } else {
                    // Look for password input in the same container
                    const container = this.closest('.password-field-container');
                    if (container) {
                        passwordField = container.querySelector('input[type="password"], input[type="text"][name*="password"]');
                    }
                }
                
                if (passwordField) {
                    const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
                    passwordField.setAttribute('type', type);
                    this.textContent = type === 'password' ? '👁️' : '🔒';
                }
            });
        });
    }

    // Highlight required fields
    const requiredInputs = document.querySelectorAll('input[required], textarea[required], select[required]');
    requiredInputs.forEach(input => {
        const formGroup = input.closest('p') || input.parentElement;
        if (formGroup) {
            formGroup.classList.add('field-required');
        }
    });

    // Validate form on submit
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const requiredFields = form.querySelectorAll('[required]');
            let formValid = true;
            
            // Clear previous error states
            form.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
            form.querySelectorAll('.error-message').forEach(el => el.remove());
            
            // Check each required field
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    formValid = false;
                    field.classList.add('error');
                    
                    // Add error message
                    const errorMsg = document.createElement('span');
                    errorMsg.classList.add('error-message');
                    errorMsg.textContent = 'Este campo es obligatorio';
                    
                    // Insert after the field
                    const fieldContainer = field.closest('p') || field.parentElement;
                    fieldContainer.appendChild(errorMsg);
                }
            });
            
            if (!formValid) {
                event.preventDefault();
                // Scroll to first error
                const firstError = form.querySelector('.error');
                if (firstError) {
                    firstError.focus();
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    });
}); 