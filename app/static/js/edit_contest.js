document.addEventListener('DOMContentLoaded', function() {
    // Initialize Quill rich text editor
    let quill = null;
    const quillContainer = document.getElementById('quill-editor');
    const textArea = document.getElementById('description_textarea');
    
    if (quillContainer && textArea) {
        // Initialize Quill with config options
        quill = new Quill(quillContainer, {
            theme: FormConfig.richTextEditor.theme,
            modules: FormConfig.richTextEditor.modules,
            placeholder: FormConfig.richTextEditor.placeholder
        });
        
        // Set initial content from textarea
        if (textArea.value) {
            quill.root.innerHTML = textArea.value;
        }
        
        // Update hidden form field before submitting the form
        const form = quillContainer.closest('form');
        if (form) {
            form.addEventListener('submit', function() {
                textArea.value = quill.root.innerHTML;
            });
        }
    }
    
    // Password visibility toggle
    const passwordToggle = document.querySelector('.password-toggle');
    const passwordInput = document.querySelector('.password-input');
    
    if (passwordToggle && passwordInput) {
        passwordToggle.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            passwordToggle.querySelector('.password-toggle-icon').textContent = 
                type === 'password' ? FormConfig.icons.passwordVisible : FormConfig.icons.passwordHidden;
        });
    }
    
    // Handle showing/hiding password field based on contest type
    const contestTypeSelect = document.querySelector('#contest_type');
    const passwordField = document.querySelector('#password-field');
    
    if (contestTypeSelect && passwordField) {
        // Initially set based on current value
        passwordField.style.display = contestTypeSelect.value === 'private' ? 'block' : 'none';
        
        // Update when changed
        contestTypeSelect.addEventListener('change', function() {
            passwordField.style.display = this.value === 'private' ? 'block' : 'none';
        });
    }
    
    // Mark required fields based on configuration
    if (FormConfig.validation && FormConfig.validation.requiredFields) {
        FormConfig.validation.requiredFields.forEach(fieldName => {
            const label = document.querySelector(`label[for="${fieldName}"]`);
            if (label) {
                label.classList.add('required-field');
            }
        });
    }
    
    // Judges selection handling
    function updateSelectedJudges() {
        const selectedJudgesList = document.getElementById('selected-judges-list');
        const aiJudgeCheckboxes = document.querySelectorAll('.ai-judge-checkbox:checked');
        const humanJudgeCheckboxes = document.querySelectorAll('.human-judge-checkbox:checked');
        const noSelectedMessage = document.querySelector('.no-selected-judges');
        
        // Clear the current list
        if (selectedJudgesList) {
            // Keep the no-selected message element
            while (selectedJudgesList.childNodes.length > 1) {
                selectedJudgesList.removeChild(selectedJudgesList.lastChild);
            }
            
            const hasSelectedJudges = aiJudgeCheckboxes.length > 0 || humanJudgeCheckboxes.length > 0;
            
            if (noSelectedMessage) {
                noSelectedMessage.style.display = hasSelectedJudges ? 'none' : 'block';
            }
            
            // Add AI judges
            aiJudgeCheckboxes.forEach(function(checkbox) {
                const judgeId = checkbox.value;
                const judgeName = checkbox.closest('label').textContent.trim();
                const modelSelector = document.querySelector(`.ai-model-selector[data-judge-id="${judgeId}"] select`);
                const modelName = modelSelector ? modelSelector.options[modelSelector.selectedIndex].text : '';
                
                const badge = document.createElement('div');
                badge.className = 'selected-judge-badge ai';
                badge.innerHTML = `${judgeName} - ${modelName} <span class="remove-judge" data-judge-id="${judgeId}">${FormConfig.icons.removeJudge}</span>`;
                selectedJudgesList.appendChild(badge);
            });
            
            // Add human judges
            humanJudgeCheckboxes.forEach(function(checkbox) {
                const judgeId = checkbox.value;
                const judgeName = checkbox.closest('label').textContent.trim();
                
                const badge = document.createElement('div');
                badge.className = 'selected-judge-badge human';
                badge.innerHTML = `${judgeName} <span class="remove-judge" data-judge-id="${judgeId}">${FormConfig.icons.removeJudge}</span>`;
                selectedJudgesList.appendChild(badge);
            });
            
            // Add event listeners to remove buttons
            document.querySelectorAll('.remove-judge').forEach(function(button) {
                button.addEventListener('click', function() {
                    const judgeId = this.getAttribute('data-judge-id');
                    const checkbox = document.querySelector(`input[name="judges"][value="${judgeId}"]`);
                    
                    if (checkbox) {
                        checkbox.checked = false;
                        
                        // Hide model selector if it's an AI judge
                        const modelSelector = document.querySelector(`.ai-model-selector[data-judge-id="${judgeId}"]`);
                        if (modelSelector) {
                            modelSelector.style.display = 'none';
                        }
                        
                        updateSelectedJudges();
                    }
                });
            });
        }
    }
    
    // Handle AI judges checkboxes
    const aiJudgeCheckboxes = document.querySelectorAll('.ai-judge-checkbox');
    
    aiJudgeCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            const judgeId = this.value;
            const modelSelector = document.querySelector(`.ai-model-selector[data-judge-id="${judgeId}"]`);
            
            if (modelSelector) {
                if (this.checked) {
                    // Show the model selector when the judge is checked
                    modelSelector.style.display = 'block';
                    
                    // Set default model if no model is selected
                    const selectElement = modelSelector.querySelector('select');
                    if (selectElement && !selectElement.value) {
                        const defaultOption = selectElement.querySelector(`option[value="${FormConfig.judgeSelection.defaultAIModel}"]`);
                        if (defaultOption) {
                            defaultOption.selected = true;
                        }
                    }
                } else {
                    // Hide the model selector when the judge is unchecked
                    modelSelector.style.display = 'none';
                }
            }
            
            updateSelectedJudges();
        });
    });
    
    // Handle model selection changes
    const modelSelects = document.querySelectorAll('.model-select');
    
    modelSelects.forEach(function(select) {
        select.addEventListener('change', function() {
            updateSelectedJudges();
        });
    });
    
    // Handle human judges checkboxes
    const humanJudgeCheckboxes = document.querySelectorAll('.human-judge-checkbox');
    
    humanJudgeCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            updateSelectedJudges();
        });
    });
    
    // Adjust judge list height based on configuration
    const judgesLists = document.querySelectorAll('.judges-list');
    judgesLists.forEach(list => {
        const judgeItems = list.querySelectorAll('.judge-item');
        const itemHeight = 40; // Approximate height of a judge item in pixels
        
        if (judgeItems.length > FormConfig.judgeSelection.maxVisibleJudges) {
            list.style.maxHeight = `${FormConfig.judgeSelection.maxVisibleJudges * itemHeight}px`;
        }
    });
    
    // Initialize selected judges display
    updateSelectedJudges();
}); 