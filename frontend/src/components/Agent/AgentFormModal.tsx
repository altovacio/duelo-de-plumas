import React, { useState, useEffect, useRef } from 'react';

interface AgentFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (agent: { 
    name: string;
    description: string;
    type: 'writer' | 'judge';
    prompt: string;
    is_public?: boolean;
  }) => void;
  initialAgent?: { 
    name: string;
    description: string;
    type: 'writer' | 'judge';
    prompt: string;
    is_public?: boolean;
    version?: string;
  };
  isEditing?: boolean;
  isAdmin?: boolean;
}

const TEMPLATE_PROMPTS = {
  writer: {
    basic: `You are a creative writer. Write a short story based on the following prompt:
\`\`\`
{{prompt}}
\`\`\`
Your story should be engaging, creative and well-structured. Keep it under 5000 words.`,
    
    poetry: `You are a poet. Write a poem based on the following prompt:
\`\`\`
{{prompt}}
\`\`\`
Your poem should evoke emotion and use vivid imagery.`,
    
    essay: `You are an essayist. Write a thoughtful essay on the following topic:
\`\`\`
{{prompt}}
\`\`\`
Your essay should be well-researched, logical, and present clear arguments.`
  },
  judge: {
    literary: `You are a literary judge evaluating texts submitted to a contest.

For each text, you will:
1. Analyze its literary merit, including style, structure, and creativity
2. Consider the originality and impact of the work
3. Evaluate how well it addresses the contest theme

Rank the top three texts and provide detailed feedback for each submission.`,
    
    technical: `You are judging texts on technical accuracy and clarity.

For each submission:
1. Evaluate the accuracy of information presented
2. Assess the clarity of explanation and logical flow
3. Consider the accessibility to the intended audience

Rank the top three texts and provide specific improvement suggestions for each.`,
    
    creative: `You are judging a creative writing contest.

For each submission:
1. Evaluate the originality and uniqueness of the concept
2. Assess character development and plot construction
3. Consider emotional impact and reader engagement

Rank the top three entries and explain your reasoning with specific examples from each text.`
  }
};

const AgentFormModal: React.FC<AgentFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialAgent = { 
    name: '', 
    description: '', 
    type: 'writer', 
    prompt: '',
    is_public: false 
  },
  isEditing = false,
  isAdmin = false,
}) => {
  // Track if this is the first render or if isOpen changed
  const firstRender = useRef(true);
  const wasOpen = useRef(isOpen);
  
  const [name, setName] = useState(initialAgent.name);
  const [description, setDescription] = useState(initialAgent.description);
  const [type, setType] = useState<'writer' | 'judge'>(initialAgent.type);
  const [prompt, setPrompt] = useState(initialAgent.prompt);
  const [isPublic, setIsPublic] = useState(initialAgent.is_public || false);
  const [selectedTemplate, setSelectedTemplate] = useState('');

  // Only update form values when the modal opens or initialAgent changes significantly
  useEffect(() => {
    // Only run this effect when modal opens or on first render with initialAgent
    if ((isOpen && !wasOpen.current) || firstRender.current) {
      setName(initialAgent.name);
      setDescription(initialAgent.description);
      setType(initialAgent.type);
      setPrompt(initialAgent.prompt);
      setIsPublic(initialAgent.is_public || false);
      setSelectedTemplate('');
      firstRender.current = false;
    }
    
    // Update the ref tracking if modal is open
    wasOpen.current = isOpen;
  }, [isOpen, initialAgent]);

  // Handle template selection
  const handleTemplateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const template = e.target.value;
    setSelectedTemplate(template);
    
    if (template && type in TEMPLATE_PROMPTS) {
      const templateType = type as keyof typeof TEMPLATE_PROMPTS;
      const templateKey = template as keyof typeof TEMPLATE_PROMPTS[typeof templateType];
      if (templateKey in TEMPLATE_PROMPTS[templateType]) {
        setPrompt(TEMPLATE_PROMPTS[templateType][templateKey]);
      }
    }
  };

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ 
      name, 
      description, 
      type,
      prompt,
      is_public: isAdmin ? isPublic : undefined
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  {isEditing ? 'Edit AI Agent' : 'Create New AI Agent'}
                </h3>
              </div>

              <div className="mb-4">
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Name
                </label>
                <input
                  type="text"
                  id="name"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  placeholder="Enter agent name"
                />
              </div>

              <div className="mb-4">
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  id="description"
                  rows={3}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  required
                  placeholder="Describe what this agent does"
                />
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700">
                  Agent Type
                </label>
                <div className="mt-1 flex space-x-4">
                  <div className="flex items-center">
                    <input
                      id="writer"
                      name="type"
                      type="radio"
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                      checked={type === 'writer'}
                      onChange={() => {
                        setType('writer');
                        setSelectedTemplate('');
                      }}
                      required
                    />
                    <label htmlFor="writer" className="ml-2 block text-sm text-gray-900">
                      Writer
                    </label>
                  </div>
                  <div className="flex items-center">
                    <input
                      id="judge"
                      name="type"
                      type="radio"
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                      checked={type === 'judge'}
                      onChange={() => {
                        setType('judge');
                        setSelectedTemplate('');
                      }}
                    />
                    <label htmlFor="judge" className="ml-2 block text-sm text-gray-900">
                      Judge
                    </label>
                  </div>
                </div>
                <p className="mt-1 text-sm text-gray-500">
                  {type === 'writer' 
                    ? 'Writer agents generate texts based on a prompt.'
                    : 'Judge agents evaluate and rank texts in a contest.'}
                </p>
              </div>

              <div className="mb-4">
                <label htmlFor="template" className="block text-sm font-medium text-gray-700">
                  Prompt Template (Optional)
                </label>
                <select
                  id="template"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  value={selectedTemplate}
                  onChange={handleTemplateChange}
                >
                  <option value="">Select a template or write your own prompt</option>
                  {type === 'writer' && (
                    <>
                      <option value="basic">Basic Story Writer</option>
                      <option value="poetry">Poetry Writer</option>
                      <option value="essay">Essay Writer</option>
                    </>
                  )}
                  {type === 'judge' && (
                    <>
                      <option value="literary">Literary Judge</option>
                      <option value="technical">Technical Judge</option>
                      <option value="creative">Creative Writing Judge</option>
                    </>
                  )}
                </select>
              </div>

              <div className="mb-4">
                <label htmlFor="prompt" className="block text-sm font-medium text-gray-700">
                  Prompt
                </label>
                <textarea
                  id="prompt"
                  rows={8}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm font-mono"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  required
                  placeholder={type === 'writer' 
                    ? 'Write instructions for generating a text...' 
                    : 'Write instructions for judging texts...'}
                />
                <p className="mt-1 text-xs text-gray-500">
                  {type === 'writer' 
                    ? 'For writer agents, you can use {{prompt}} to indicate where user input should be inserted.' 
                    : 'For judge agents, your prompt should describe the evaluation criteria and ranking process.'}
                </p>
              </div>

              {isAdmin && (
                <div className="mb-4">
                  <div className="flex items-center">
                    <input
                      id="is_public"
                      name="is_public"
                      type="checkbox"
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      checked={isPublic}
                      onChange={(e) => setIsPublic(e.target.checked)}
                    />
                    <label htmlFor="is_public" className="ml-2 block text-sm text-gray-900">
                      Make Public
                    </label>
                  </div>
                  <p className="mt-1 text-sm text-gray-500">
                    Public agents can be viewed and cloned by all users.
                  </p>
                </div>
              )}
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm"
              >
                {isEditing ? 'Save Changes' : 'Create Agent'}
              </button>
              <button
                type="button"
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                onClick={onClose}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AgentFormModal; 