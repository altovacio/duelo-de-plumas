/**
 * Submission Form Implementation with Quill Editor
 * 
 * This script initializes the rich text editor for user submissions
 * and handles form submission and validation.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a submission form page
    const submissionContainer = document.getElementById('submission-editor');
    const submissionContent = document.getElementById('text_content');
    
    if (!submissionContainer || !submissionContent) {
        return; // Not on a submission form page
    }
    
    // Add the container class for styling
    submissionContainer.classList.add('quill-editor-container');
    submissionContainer.classList.add('submission');
    
    // Create a character counter element
    const charCounter = document.createElement('div');
    charCounter.classList.add('quill-char-counter');
    submissionContainer.parentNode.insertBefore(charCounter, submissionContainer.nextSibling);
    
    // Initialize the Quill editor
    const quillEditor = QuillConfig.initialize('submission', 'submission-editor', 'text_content', {
        onTextChange: function(delta, html) {
            // Update character counter
            updateCharCounter(quillEditor.getText().length);
        }
    });
    
    // Update character counter initially
    updateCharCounter(quillEditor.getText().length);
    
    // Function to update character counter
    function updateCharCounter(length) {
        const maxLength = QuillConfig.maxLength.submission;
        const remaining = maxLength - length;
        
        charCounter.textContent = `${length} / ${maxLength} caracteres`;
        
        // Add warning classes based on how close to the limit
        charCounter.classList.remove('near-limit', 'at-limit');
        
        if (length > maxLength) {
            charCounter.classList.add('at-limit');
        } else if (length > maxLength * 0.9) {
            charCounter.classList.add('near-limit');
        }
    }
    
    // Handle form submission
    const submissionForm = document.querySelector('form');
    if (submissionForm) {
        submissionForm.addEventListener('submit', function(e) {
            // Get current text length
            const textLength = quillEditor.getText().length;
            const maxLength = QuillConfig.maxLength.submission;
            
            // Validate content length
            if (textLength > maxLength) {
                e.preventDefault();
                alert(`El texto es demasiado largo. El límite es de ${maxLength} caracteres.`);
                return false;
            }
            
            // Check if the editor is empty
            if (textLength <= 1) { // Quill adds a newline character
                e.preventDefault();
                alert('Por favor, escribe un texto antes de enviar.');
                return false;
            }
            
            // Set the hidden input value with HTML content
            submissionContent.value = quillEditor.getHTML();
            
            // Let the form submit
            return true;
        });
    }
}); 