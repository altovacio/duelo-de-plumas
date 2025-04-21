/**
 * Contest Editor Enhancement
 * 
 * This script adds character counter functionality to the contest description editor
 * using the modular Quill editor system.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a contest edit page
    const quillEditor = document.getElementById('quill-editor');
    if (!quillEditor) return;
    
    // Get the Quill instance and add a character counter
    const quillInstance = Quill.find(quillEditor);
    if (!quillInstance) return;
    
    // Create a character counter element
    const charCounter = document.createElement('div');
    charCounter.classList.add('quill-char-counter');
    quillEditor.parentNode.insertBefore(charCounter, quillEditor.nextSibling);
    
    // Get maximum length from QuillConfig
    const maxLength = typeof QuillConfig !== 'undefined' ? 
        QuillConfig.maxLength.contest : 10000;
    
    // Update character counter initially and on changes
    function updateCharCounter() {
        const length = quillInstance.getText().length;
        charCounter.textContent = `${length} / ${maxLength} caracteres`;
        
        // Add warning classes based on how close to the limit
        charCounter.classList.remove('near-limit', 'at-limit');
        
        if (length > maxLength) {
            charCounter.classList.add('at-limit');
        } else if (length > maxLength * 0.9) {
            charCounter.classList.add('near-limit');
        }
    }
    
    // Update initially
    updateCharCounter();
    
    // Update on text changes
    quillInstance.on('text-change', updateCharCounter);
    
    // Add a form submission handler to validate length
    const form = quillEditor.closest('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const length = quillInstance.getText().length;
            
            if (length > maxLength) {
                e.preventDefault();
                alert(`La descripción es demasiado larga. El límite es de ${maxLength} caracteres.`);
                return false;
            }
            
            return true;
        });
    }
}); 