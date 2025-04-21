/**
 * Judge Comment Implementation with Quill Editor
 * 
 * This script initializes the rich text editor for judge comments
 * and handles form submission and validation.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find all comment editors in the page
    const commentContainers = document.querySelectorAll('.comment-editor-container');
    
    if (commentContainers.length === 0) {
        return; // No comment editors on this page
    }
    
    // Initialize each comment editor
    commentContainers.forEach(function(container) {
        const commentId = container.dataset.commentId;
        const editorId = `comment-editor-${commentId}`;
        const textareaId = `comment-${commentId}`;
        
        // Create the editor div
        const editorDiv = document.createElement('div');
        editorDiv.id = editorId;
        editorDiv.classList.add('quill-editor-container');
        editorDiv.classList.add('comment');
        
        // Replace the textarea with the editor div
        const textarea = document.getElementById(textareaId);
        if (!textarea) {
            console.error(`Textarea with ID ${textareaId} not found`);
            return;
        }
        
        const textareaValue = textarea.value;
        textarea.style.display = 'none';
        container.insertBefore(editorDiv, textarea);
        
        // Create a character counter element
        const charCounter = document.createElement('div');
        charCounter.classList.add('quill-char-counter');
        charCounter.id = `char-counter-${commentId}`;
        container.appendChild(charCounter);
        
        // Initialize the Quill editor
        const quillEditor = QuillConfig.initialize('comment', editorId, textareaId, {
            onTextChange: function(delta, html) {
                // Update character counter
                updateCharCounter(commentId, quillEditor);
            }
        });
        
        // Set initial content if textarea has value
        if (textareaValue) {
            quillEditor.setHTML(textareaValue);
        }
        
        // Update character counter initially
        updateCharCounter(commentId, quillEditor);
    });
    
    // Function to update character counter
    function updateCharCounter(commentId, editor) {
        const length = editor.getText().length;
        const maxLength = QuillConfig.maxLength.comment;
        const counter = document.getElementById(`char-counter-${commentId}`);
        
        if (!counter) return;
        
        counter.textContent = `${length} / ${maxLength} caracteres`;
        
        // Add warning classes based on how close to the limit
        counter.classList.remove('near-limit', 'at-limit');
        
        if (length > maxLength) {
            counter.classList.add('at-limit');
        } else if (length > maxLength * 0.9) {
            counter.classList.add('near-limit');
        }
    }
    
    // Handle form submission
    const evaluationForm = document.querySelector('form');
    if (evaluationForm) {
        evaluationForm.addEventListener('submit', function(e) {
            let hasError = false;
            
            // Check each editor for length validation
            commentContainers.forEach(function(container) {
                const commentId = container.dataset.commentId;
                const textareaId = `comment-${commentId}`;
                const editorId = `comment-editor-${commentId}`;
                
                // Find the associated editor
                const editorContainer = document.getElementById(editorId);
                if (!editorContainer) return;
                
                // Get the Quill instance from the DOM element
                const quillInstance = Quill.find(editorContainer);
                if (!quillInstance) return;
                
                // Get current text length
                const textLength = quillInstance.getText().length;
                const maxLength = QuillConfig.maxLength.comment;
                
                // Validate content length
                if (textLength > maxLength) {
                    e.preventDefault();
                    alert(`El comentario para la sumisión ${commentId} es demasiado largo. El límite es de ${maxLength} caracteres.`);
                    hasError = true;
                    return false;
                }
            });
            
            if (hasError) {
                return false;
            }
            
            // Let the form submit
            return true;
        });
    }
}); 