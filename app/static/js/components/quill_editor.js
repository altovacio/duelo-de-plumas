/**
 * QuillEditor - A reusable rich text editor component
 * This component wraps Quill.js to provide a consistent interface
 * for rich text editing throughout the application.
 */
class QuillEditor {
    /**
     * Creates a new QuillEditor instance
     * @param {Object} options - Configuration options
     * @param {HTMLElement|string} options.container - The container element or its ID
     * @param {HTMLElement|string} options.textarea - The textarea element or its ID to sync with
     */
    constructor(options) {
        // Get container element
        this.container = typeof options.container === 'string' 
            ? document.getElementById(options.container) 
            : options.container;
        
        // Get textarea element
        this.textarea = typeof options.textarea === 'string' 
            ? document.getElementById(options.textarea) 
            : options.textarea;
        
        // Store form reference
        this.form = this.textarea ? this.textarea.closest('form') : null;
        
        // Initialize Quill instance
        this._initQuill();
        
        // Set initial content if textarea has value
        if (this.textarea && this.textarea.value) {
            this.quill.root.innerHTML = this.textarea.value;
        }
    }
    
    /**
     * Initializes the Quill editor instance
     * @private
     */
    _initQuill() {
        if (!this.container) {
            console.error('QuillEditor: Container element not found');
            return;
        }
        
        // Create Quill instance with default config
        this.quill = new Quill(this.container, {
            theme: 'snow',
            modules: {
                toolbar: [
                    // Basic formatting
                    ['bold', 'italic', 'underline', 'strike'],
                    
                    // Alignment
                    [{ 'align': ['', 'center', 'right', 'justify'] }],
                    
                    // Quote format
                    ['blockquote'],
                    
                    // Lists
                    [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                    
                    // Headers
                    [{ 'header': [1, 2, 3, false] }],
                    
                    // Clean formatting
                    ['clean']
                ]
            },
            placeholder: typeof FormConfig !== 'undefined' && FormConfig.richTextEditor ? 
                FormConfig.richTextEditor.placeholder : 'Escribe aquí...'
        });
        
        // Set up event listeners
        if (this.form && this.textarea) {
            this.form.addEventListener('submit', () => {
                this.textarea.value = this.quill.root.innerHTML;
            });
        }
    }
    
    /**
     * Gets the Quill instance
     * @returns {Quill} - The Quill instance
     */
    getInstance() {
        return this.quill;
    }
    
    /**
     * Gets the current content
     * @returns {string} - The HTML content
     */
    getContent() {
        return this.quill ? this.quill.root.innerHTML : '';
    }
    
    /**
     * Sets the content
     * @param {string} html - The HTML content to set
     */
    setContent(html) {
        if (this.quill) {
            this.quill.root.innerHTML = html;
        }
    }
    
    /**
     * Syncs editor content to the associated textarea
     */
    syncToTextarea() {
        if (this.textarea && this.quill) {
            this.textarea.value = this.quill.root.innerHTML;
        }
    }
    
    /**
     * Enables the editor
     */
    enable() {
        if (this.quill) {
            this.quill.enable();
        }
    }
    
    /**
     * Disables the editor
     */
    disable() {
        if (this.quill) {
            this.quill.disable();
        }
    }
}

// Export the QuillEditor class for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QuillEditor;
} 