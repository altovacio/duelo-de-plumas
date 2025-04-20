/**
 * Configuration file for contest form parameters
 * This file contains settings that might need to be changed by administrators
 */

const FormConfig = {
    // Quill Editor Settings
    richTextEditor: {
        theme: 'snow',
        modules: {
            toolbar: [
                ['bold', 'italic', 'underline', 'strike'],
                ['blockquote', 'code-block'],
                [{ 'header': 1 }, { 'header': 2 }],
                [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                [{ 'script': 'sub' }, { 'script': 'super' }],
                [{ 'indent': '-1' }, { 'indent': '+1' }],
                [{ 'direction': 'rtl' }],
                [{ 'size': ['small', false, 'large', 'huge'] }],
                [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
                [{ 'color': [] }, { 'background': [] }],
                [{ 'font': [] }],
                [{ 'align': [] }],
                ['clean']
            ]
        },
        placeholder: 'Escribe la descripción del concurso aquí...',
    },
    
    // Judge Selection Settings
    judgeSelection: {
        maxVisibleJudges: 15,  // Maximum number of judges to display without scrolling
        defaultAIModel: 'claude-3-5-haiku-latest' // Default AI model to select
    },
    
    // Icons and Symbols
    icons: {
        passwordVisible: '👁️',
        passwordHidden: '🔒',
        removeJudge: '×'
    },
    
    // Validation Settings
    validation: {
        requiredFields: [
            'title',
            'description',
            'end_date',
            'required_judges',
            'contest_type',
            'status'
        ]
    }
}; 