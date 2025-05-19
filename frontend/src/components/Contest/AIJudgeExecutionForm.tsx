import React, { useState, useEffect } from 'react';
import { Agent, executeJudgeAgent } from '../../services/agentService';
import { getAgents } from '../../services/agentService';
import { getModels, LLMModel, estimateCost } from '../../services/modelService';

interface AIJudgeExecutionFormProps {
  contestId: number;
  contestTextCount: number;
  averageTextLength: number;
  onSuccess: () => void;
  onCancel: () => void;
}

const AIJudgeExecutionForm: React.FC<AIJudgeExecutionFormProps> = ({
  contestId,
  contestTextCount,
  averageTextLength,
  onSuccess,
  onCancel
}) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [models, setModels] = useState<LLMModel[]>([]);
  
  const [selectedAgentId, setSelectedAgentId] = useState<number | ''>('');
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  
  const [estimatedCost, setEstimatedCost] = useState<number | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [loadingAgents, setLoadingAgents] = useState(false);
  const [loadingModels, setLoadingModels] = useState(false);
  
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  
  // Load judge agents and models
  useEffect(() => {
    const fetchAgentsAndModels = async () => {
      try {
        // Fetch judge agents
        setLoadingAgents(true);
        const response = await getAgents();
        const judgeAgents = response.filter(agent => agent.type === 'judge');
        setAgents(judgeAgents);
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
  
  // Calculate cost estimate when agent, model, or text stats change
  useEffect(() => {
    if (selectedModelId && models.length > 0) {
      const selectedModel = models.find(model => model.id === selectedModelId);
      
      if (selectedModel) {
        // Total length of all texts * average text length * number of texts to review
        const totalInputLength = contestTextCount * averageTextLength;
        
        // Estimate output length - 3 places with comments
        const estimatedOutputLength = 1000; // Roughly 1000 characters for response with 3 rankings
        
        const cost = estimateCost(selectedModel, totalInputLength, estimatedOutputLength);
        setEstimatedCost(cost);
      }
    }
  }, [selectedModelId, models, contestTextCount, averageTextLength]);
  
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
      setError('Please select an AI judge.');
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
      
      // Execute the AI judge
      await executeJudgeAgent({
        agent_id: Number(selectedAgentId),
        model: selectedModelId,
        contest_id: contestId
      });
      
      // Set progress to 100% on success
      setProgress(100);
      
      // Allow the progress bar to reach 100% before closing
      setTimeout(() => {
        setIsExecuting(false);
        onSuccess();
      }, 1000);
    } catch (err: any) {
      console.error('Error executing AI judge:', err);
      setError(err.response?.data?.message || 'Failed to execute AI judge. Please try again.');
      setIsExecuting(false);
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-6 max-w-lg mx-auto">
      <h2 className="text-xl font-bold mb-4">Execute AI Judge</h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
          {error}
        </div>
      )}
      
      {isExecuting ? (
        <div>
          <p className="text-gray-700 mb-2">Executing AI Judge...</p>
          <div className="w-full bg-gray-200 rounded-full h-2.5 mb-4">
            <div 
              className="bg-indigo-600 h-2.5 rounded-full" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-500">
            This may take several minutes depending on the size of the contest.
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="agent-select" className="block text-sm font-medium text-gray-700 mb-1">
              Select AI Judge
            </label>
            
            {loadingAgents ? (
              <p className="text-gray-500">Loading AI judges...</p>
            ) : agents.length === 0 ? (
              <p className="text-gray-500 mb-2">No judge agents available. Please create one first.</p>
            ) : (
              <select
                id="agent-select"
                className="w-full p-2 border rounded-md"
                value={selectedAgentId}
                onChange={(e) => setSelectedAgentId(Number(e.target.value))}
              >
                <option value="">-- Select an AI judge --</option>
                {agents.map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name}
                  </option>
                ))}
              </select>
            )}
          </div>
          
          <div className="mb-6">
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
          
          {estimatedCost !== null && (
            <div className="mb-6 p-4 bg-blue-50 rounded-md">
              <h3 className="font-medium text-blue-800 mb-1">Cost Estimate</h3>
              <p className="text-blue-700">
                This operation will use approximately{' '}
                <span className="font-bold">${estimatedCost.toFixed(4)}</span> credits
                to judge {contestTextCount} texts.
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
              Execute AI Judge
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default AIJudgeExecutionForm; 