import React, { useState, useEffect } from 'react';
import { Agent, executeWriterAgent } from '../../services/agentService';
import { getAgents } from '../../services/agentService';
import { getModels, LLMModel, estimateCost } from '../../services/modelService';
import { createText } from '../../services/textService';

interface AIWriterExecutionFormProps {
  contestId?: number; // Optional - if provided, context for the writing
  contestTitle?: string;
  contestDescription?: string;
  onSuccess: (textId?: number) => void;
  onCancel: () => void;
}

const AIWriterExecutionForm: React.FC<AIWriterExecutionFormProps> = ({
  contestId,
  contestTitle,
  contestDescription,
  onSuccess,
  onCancel
}) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [models, setModels] = useState<LLMModel[]>([]);
  
  const [selectedAgentId, setSelectedAgentId] = useState<number | ''>('');
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  const [title, setTitle] = useState<string>('');
  const [customPrompt, setCustomPrompt] = useState<string>('');
  
  const [generatedText, setGeneratedText] = useState<string>('');
  const [estimatedCost, setEstimatedCost] = useState<number | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [loadingAgents, setLoadingAgents] = useState(false);
  const [loadingModels, setLoadingModels] = useState(false);
  
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  
  // Flag to show preview after generation
  const [showPreview, setShowPreview] = useState(false);
  
  // Load writer agents and models
  useEffect(() => {
    const fetchAgentsAndModels = async () => {
      try {
        // Fetch writer agents
        setLoadingAgents(true);
        const response = await getAgents();
        const writerAgents = response.filter(agent => agent.type === 'writer');
        setAgents(writerAgents);
        setLoadingAgents(false);
        
        // Fetch available models
        setLoadingModels(true);
        const modelsResponse = await getModels();
        setModels(modelsResponse);
        
        // Set default model if available
        if (modelsResponse.length > 0) {
          setSelectedModelId(modelsResponse[0].id);
        }
        setLoadingModels(false);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to load agents or models. Please try again.');
        setLoadingAgents(false);
        setLoadingModels(false);
      }
    };
    
    fetchAgentsAndModels();
  }, []);
  
  // Calculate cost estimate when model changes
  useEffect(() => {
    if (selectedModelId && models.length > 0) {
      const selectedModel = models.find(model => model.id === selectedModelId);
      
      if (selectedModel) {
        // Calculate input length for cost estimation
        let inputLength = customPrompt.length;
        if (contestTitle) inputLength += contestTitle.length;
        if (contestDescription) inputLength += contestDescription.length;
        
        // Estimated output is typically longer for creative writing
        const estimatedOutputLength = 3000; // Roughly 3000 characters for a short story/poem
        
        const cost = estimateCost(selectedModel, inputLength, estimatedOutputLength);
        setEstimatedCost(cost);
      }
    }
  }, [selectedModelId, models, customPrompt, contestTitle, contestDescription]);
  
  // Simulate AI execution progress
  useEffect(() => {
    let progressInterval: NodeJS.Timeout;
    
    if (isExecuting) {
      progressInterval = setInterval(() => {
        setProgress(prev => {
          // Cap at 90% until we get a real success response
          return prev < 90 ? prev + 5 : prev;
        });
      }, 1000);
    }
    
    return () => {
      if (progressInterval) clearInterval(progressInterval);
    };
  }, [isExecuting]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedAgentId) {
      setError('Please select an AI writer.');
      return;
    }
    
    if (!selectedModelId) {
      setError('Please select a model.');
      return;
    }
    
    try {
      setIsExecuting(true);
      setError(null);
      setProgress(0);
      
      // Execute the AI writer
      const result = await executeWriterAgent({
        agent_id: Number(selectedAgentId),
        model: selectedModelId,
        title: title || contestTitle,
        description: customPrompt,
        contest_description: contestDescription
      });
      
      // Simulate getting generated text from the result
      // In a real implementation, you'd get this from the API response
      const mockGeneratedText = 
        "This is a sample generated text from the AI writer.\n\n" +
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus lacinia odio vitae vestibulum.\n\n" +
        "Donec in efficitur leo. In hac habitasse platea dictumst. Morbi condimentum, neque ac porttitor scelerisque.\n\n" +
        "Interdum et malesuada fames ac ante ipsum primis in faucibus.";
      
      setGeneratedText(mockGeneratedText);
      
      // Set progress to 100% on success
      setProgress(100);
      
      // Show the preview
      setTimeout(() => {
        setIsExecuting(false);
        setShowPreview(true);
      }, 1000);
    } catch (err: any) {
      console.error('Error executing AI writer:', err);
      setError(err.response?.data?.message || 'Failed to execute AI writer. Please try again.');
      setIsExecuting(false);
    }
  };
  
  const handleSaveText = async () => {
    try {
      setIsExecuting(true);
      
      // Save the generated text as a new text
      const newText = await createText({
        title: title || `Generated text ${new Date().toLocaleString()}`,
        content: generatedText,
        author: 'AI Writer'
      });
      
      setIsExecuting(false);
      onSuccess(newText.id);
    } catch (err: any) {
      console.error('Error saving text:', err);
      setError(err.response?.data?.message || 'Failed to save text. Please try again.');
      setIsExecuting(false);
    }
  };
  
  // Show the text preview after generation
  if (showPreview) {
    return (
      <div className="bg-white rounded-lg shadow p-6 max-w-lg mx-auto">
        <h2 className="text-xl font-bold mb-4">Generated Text</h2>
        
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
            {error}
          </div>
        )}
        
        <div className="mb-4">
          <label htmlFor="title-input" className="block text-sm font-medium text-gray-700 mb-1">
            Title
          </label>
          <input
            id="title-input"
            type="text"
            className="w-full p-2 border rounded-md"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter a title for this text"
          />
        </div>
        
        <div className="mb-6">
          <label htmlFor="generated-text" className="block text-sm font-medium text-gray-700 mb-1">
            Generated Content
          </label>
          <div className="w-full p-4 border rounded-md bg-gray-50 max-h-96 overflow-y-auto">
            <pre className="whitespace-pre-wrap">{generatedText}</pre>
          </div>
        </div>
        
        <div className="flex justify-between space-x-3">
          <button
            type="button"
            className="py-2 px-4 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
            onClick={() => {
              setShowPreview(false);
              setGeneratedText('');
            }}
          >
            Generate Again
          </button>
          
          <div className="space-x-3">
            <button
              type="button"
              className="py-2 px-4 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
              onClick={onCancel}
            >
              Discard
            </button>
            
            <button
              type="button"
              className="py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-indigo-300"
              onClick={handleSaveText}
              disabled={isExecuting}
            >
              Save Text
            </button>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg shadow p-6 max-w-lg mx-auto">
      <h2 className="text-xl font-bold mb-4">Execute AI Writer</h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
          {error}
        </div>
      )}
      
      {isExecuting ? (
        <div>
          <p className="text-gray-700 mb-2">Generating Text...</p>
          <div className="w-full bg-gray-200 rounded-full h-2.5 mb-4">
            <div 
              className="bg-indigo-600 h-2.5 rounded-full" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-500">
            Please wait while the AI generates your text. This may take a minute or two.
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="agent-select" className="block text-sm font-medium text-gray-700 mb-1">
              Select AI Writer
            </label>
            
            {loadingAgents ? (
              <p className="text-gray-500">Loading AI writers...</p>
            ) : agents.length === 0 ? (
              <p className="text-gray-500 mb-2">No writer agents available. Please create one first.</p>
            ) : (
              <select
                id="agent-select"
                className="w-full p-2 border rounded-md"
                value={selectedAgentId}
                onChange={(e) => setSelectedAgentId(Number(e.target.value))}
              >
                <option value="">-- Select an AI writer --</option>
                {agents.map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name}
                  </option>
                ))}
              </select>
            )}
          </div>
          
          <div className="mb-4">
            <label htmlFor="model-select" className="block text-sm font-medium text-gray-700 mb-1">
              Select Model
            </label>
            
            {loadingModels ? (
              <p className="text-gray-500">Loading models...</p>
            ) : models.length === 0 ? (
              <p className="text-gray-500 mb-2">No models available.</p>
            ) : (
              <select
                id="model-select"
                className="w-full p-2 border rounded-md"
                value={selectedModelId}
                onChange={(e) => setSelectedModelId(e.target.value)}
              >
                {models.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name} ({model.provider})
                  </option>
                ))}
              </select>
            )}
          </div>
          
          {contestTitle && contestDescription && (
            <div className="mb-4 p-4 bg-gray-50 rounded-md">
              <h3 className="font-medium text-gray-800 mb-1">Contest Context</h3>
              <p className="text-gray-700 text-sm mb-1">
                <span className="font-medium">Title:</span> {contestTitle}
              </p>
              <p className="text-gray-700 text-sm">
                <span className="font-medium">Description:</span> {contestDescription}
              </p>
            </div>
          )}
          
          <div className="mb-4">
            <label htmlFor="title-input" className="block text-sm font-medium text-gray-700 mb-1">
              Title for Generated Text (Optional)
            </label>
            <input
              id="title-input"
              type="text"
              className="w-full p-2 border rounded-md"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter a title or leave blank to auto-generate"
            />
          </div>
          
          <div className="mb-6">
            <label htmlFor="custom-prompt" className="block text-sm font-medium text-gray-700 mb-1">
              Custom Instructions (Optional)
            </label>
            <textarea
              id="custom-prompt"
              rows={4}
              className="w-full p-2 border rounded-md"
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              placeholder="Add any specific instructions or context for the AI writer..."
            />
          </div>
          
          {estimatedCost !== null && (
            <div className="mb-6 p-4 bg-blue-50 rounded-md">
              <h3 className="font-medium text-blue-800 mb-1">Cost Estimate</h3>
              <p className="text-blue-700">
                This operation will use approximately{' '}
                <span className="font-bold">${estimatedCost.toFixed(4)}</span> credits.
              </p>
            </div>
          )}
          
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              className="py-2 px-4 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
              onClick={onCancel}
            >
              Cancel
            </button>
            
            <button
              type="submit"
              className="py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-indigo-300"
              disabled={!selectedAgentId || !selectedModelId || loadingAgents || loadingModels}
            >
              Generate Text
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default AIWriterExecutionForm; 