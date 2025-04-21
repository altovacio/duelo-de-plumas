// Placeholder for future JavaScript enhancements
console.log("Duelo de Plumas script loaded.");

// Form validation and UI enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Password visibility toggle
    const passwordToggles = document.querySelectorAll('.password-toggle');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const passwordField = this.previousElementSibling;
            const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordField.setAttribute('type', type);
            this.textContent = type === 'password' ? '👁️' : '🔒';
        });
    });

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