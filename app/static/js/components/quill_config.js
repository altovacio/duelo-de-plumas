/**
 * Quill Editor Configuration Module
 * 
 * This module contains configurable parameters for the Quill editor
 * implementation. Modify these values to adjust the editor's behavior
 * without changing the editor component itself.
 */

const QuillConfig = {
    /**
     * Maximum text length for different editor modes
     */
    maxLength: {
        submission: 20000, // Maximum length for user submissions
        comment: 2000,     // Maximum length for judge comments
        contest: 10000     // Maximum length for contest descriptions
    },
    
    /**
     * Placeholder texts for different editor modes
     */
    placeholder: {
        submission: 'Escribe aquí tu texto literario...',
        comment: 'Escribe aquí tu comentario sobre este texto...',
        contest: 'Describe el concurso aquí...'
    },
    
    /**
     * Custom toolbar configurations
     * Override the default toolbar configurations in ModularQuillEditor
     */
    toolbar: {
        // Full toolbar for submissions and contest edits
        submission: [
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
        ],
        
        // Use the same toolbar for contest edits
        contest: [
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
        ],
        
        // Simpler toolbar for comments (now with strikethrough)
        comment: [
            ['bold', 'italic', 'underline', 'strike'], // Added strike
            ['blockquote'],
            [{ 'list': 'ordered'}, { 'list': 'bullet' }],
            [{ 'color': [] }],
            ['clean']
        ]
    },
    
    /**
     * Custom Quill module configuration
     */
    modules: {
        submission: {
            // You can add custom modules here
        },
        comment: {
            // You can add custom modules here
        },
        contest: {
            // You can add custom modules here
        }
    },
    
    /**
     * Default themes
     */
    theme: {
        submission: 'snow',
        comment: 'snow',
        contest: 'snow'
    },
    
    /**
     * CSS class names
     */
    css: {
        containerClass: 'quill-editor-container',
        editorClass: 'quill-editor'
    },
    
    /**
     * Debug mode settings
     */
    debug: false,
    
    /**
     * Initialize a Quill editor with preset configurations
     * @param {string} mode - 'submission', 'comment', or 'contest'
     * @param {string} containerId - ID of the container element
     * @param {string} hiddenInputId - ID of the hidden input to store content
     * @param {Object} customOptions - Optional custom options to override defaults
     * @returns {ModularQuillEditor} Initialized Quill editor instance
     */
    initialize(mode, containerId, hiddenInputId, customOptions = {}) {
        // Validate parameters
        if (!['submission', 'comment', 'contest'].includes(mode)) {
            console.error(`Invalid Quill editor mode: ${mode}. Must be 'submission', 'comment', or 'contest'.`);
            return null;
        }
        
        if (!containerId || !hiddenInputId) {
            console.error('Container ID and hidden input ID are required to initialize Quill editor.');
            return null;
        }
        
        // Base configuration
        const config = {
            container: `#${containerId}`,
            hiddenInput: `#${hiddenInputId}`,
            mode: mode,
            placeholder: this.placeholder[mode],
            maxLength: this.maxLength[mode],
            toolbarOptions: this.toolbar[mode],
            quillOptions: {
                theme: this.theme[mode],
                modules: {
                    toolbar: this.toolbar[mode],
                    ...this.modules[mode]
                }
            }
        };
        
        // Merge with custom options
        const finalConfig = { ...config, ...customOptions };
        
        // Create and return ModularQuillEditor instance
        if (typeof ModularQuillEditor === 'undefined') {
            console.error('ModularQuillEditor class is not loaded. Make sure to include quill_editor.js before quill_config.js');
            return null;
        }
        
        return new ModularQuillEditor(finalConfig);
    }
}; 