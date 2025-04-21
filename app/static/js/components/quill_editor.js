/**
 * ModularQuillEditor - A reusable Quill rich text editor component
 * 
 * This component can be used for both user submissions and judge comments
 * with configurable toolbar options and settings.
 */
class ModularQuillEditor {
    /**
     * Create a new ModularQuillEditor instance
     * @param {Object} options - Configuration options
     * @param {string|HTMLElement} options.container - The container element or selector
     * @param {string|HTMLElement} options.hiddenInput - The hidden input element or selector to store content
     * @param {Object} options.toolbarOptions - Custom toolbar options (optional)
     * @param {Object} options.quillOptions - Additional Quill options (optional)
     * @param {Function} options.onTextChange - Callback for text-change event (optional)
     * @param {string} options.placeholder - Placeholder text (optional)
     * @param {string} options.mode - 'submission', 'comment', or 'contest' to use preset configurations
     * @param {number} options.maxLength - Maximum text length (optional)
     */
    constructor(options) {
        this.options = options;
        this.container = typeof options.container === 'string' 
            ? document.querySelector(options.container) 
            : options.container;
        
        this.hiddenInput = typeof options.hiddenInput === 'string' 
            ? document.querySelector(options.hiddenInput) 
            : options.hiddenInput;
        
        if (!this.container) {
            console.error('ModularQuillEditor: Container element not found');
            return;
        }
        
        if (!this.hiddenInput) {
            console.error('ModularQuillEditor: Hidden input element not found');
            return;
        }
        
        // Set default toolbar options based on mode
        let defaultToolbarOptions;
        if (options.mode === 'submission') {
            defaultToolbarOptions = [
                ['bold', 'italic', 'underline', 'strike'],
                ['blockquote', 'code-block'],
                [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
                [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                [{ 'script': 'sub'}, { 'script': 'super' }],
                [{ 'indent': '-1'}, { 'indent': '+1' }],
                [{ 'size': ['small', false, 'large', 'huge'] }],
                [{ 'color': [] }, { 'background': [] }],
                [{ 'font': [] }],
                [{ 'align': [] }],
                ['clean']
            ];
        } else if (options.mode === 'contest') {
            // Same toolbar as submission for contest descriptions
            defaultToolbarOptions = [
                ['bold', 'italic', 'underline', 'strike'],
                ['blockquote', 'code-block'],
                [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
                [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                [{ 'script': 'sub'}, { 'script': 'super' }],
                [{ 'indent': '-1'}, { 'indent': '+1' }],
                [{ 'size': ['small', false, 'large', 'huge'] }],
                [{ 'color': [] }, { 'background': [] }],
                [{ 'font': [] }],
                [{ 'align': [] }],
                ['clean']
            ];
        } else if (options.mode === 'comment') {
            // Simpler toolbar for comments
            defaultToolbarOptions = [
                ['bold', 'italic', 'underline', 'strike'],
                ['blockquote'],
                [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                [{ 'color': [] }],
                ['clean']
            ];
        } else {
            // Basic default toolbar
            defaultToolbarOptions = [
                ['bold', 'italic', 'underline'],
                [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                ['clean']
            ];
        }
        
        const toolbarOptions = options.toolbarOptions || defaultToolbarOptions;
        
        // Set default Quill options
        const defaultQuillOptions = {
            modules: {
                toolbar: toolbarOptions
            },
            theme: 'snow',
            placeholder: options.placeholder || 'Escribe aquí...'
        };
        
        // Merge default options with user options
        const quillOptions = { ...defaultQuillOptions, ...(options.quillOptions || {}) };
        
        // Initialize Quill
        this.quill = new Quill(this.container, quillOptions);
        
        // Set initial content if hidden input has value
        if (this.hiddenInput.value) {
            try {
                // Try to parse as delta if it starts with '{"ops":'
                if (this.hiddenInput.value.trim().startsWith('{"ops":')) {
                    const delta = JSON.parse(this.hiddenInput.value);
                    this.quill.setContents(delta);
                } else {
                    // Otherwise set as HTML
                    this.quill.root.innerHTML = this.hiddenInput.value;
                }
            } catch (e) {
                console.error('Error setting initial Quill content:', e);
                // Fallback: set as text
                this.quill.setText(this.hiddenInput.value);
            }
        }
        
        // Set up max length if specified
        this.maxLength = options.maxLength || null;
        
        // Set up event listeners
        this.setupEventListeners();
    }
    
    /**
     * Set up event listeners for the editor
     */
    setupEventListeners() {
        // Update hidden input on text-change
        this.quill.on('text-change', () => {
            // Check max length if specified
            if (this.maxLength) {
                const text = this.quill.getText();
                if (text.length > this.maxLength) {
                    // Truncate content if too long
                    const delta = this.quill.getContents();
                    this.quill.setText(text.slice(0, this.maxLength));
                    return;
                }
            }
            
            // Update hidden input with HTML content
            this.hiddenInput.value = this.quill.root.innerHTML;
            
            // Call user callback if provided
            if (typeof this.options.onTextChange === 'function') {
                this.options.onTextChange(this.quill.getContents(), this.quill.root.innerHTML);
            }
        });
    }
    
    /**
     * Get the Quill instance
     * @returns {Quill} The Quill instance
     */
    getQuill() {
        return this.quill;
    }
    
    /**
     * Get the editor's content as HTML
     * @returns {string} HTML content
     */
    getHTML() {
        return this.quill.root.innerHTML;
    }
    
    /**
     * Get the editor's content as text
     * @returns {string} Text content
     */
    getText() {
        return this.quill.getText();
    }
    
    /**
     * Get the editor's content as a Delta object
     * @returns {Object} Delta object
     */
    getContents() {
        return this.quill.getContents();
    }
    
    /**
     * Set the editor's content as HTML
     * @param {string} html - HTML content
     */
    setHTML(html) {
        this.quill.root.innerHTML = html;
        this.hiddenInput.value = html;
    }
    
    /**
     * Set the editor's content as text
     * @param {string} text - Text content
     */
    setText(text) {
        this.quill.setText(text);
        this.hiddenInput.value = this.quill.root.innerHTML;
    }
    
    /**
     * Clear the editor's content
     */
    clear() {
        this.quill.setText('');
        this.hiddenInput.value = '';
    }
} 