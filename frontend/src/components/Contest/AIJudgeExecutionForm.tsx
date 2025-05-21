import React, { useState, useEffect } from 'react';
import { Agent, executeJudgeAgent } from '../../services/agentService';
import { getAgents } from '../../services/agentService';
import { getModels, LLMModel, estimateCost } from '../../services/modelService';
import { useAuthStore } from '../../store/authStore';
import { useForm, Controller } from 'react-hook-form';

interface AIJudgeExecutionFormProps {
  contestId: number;
  contestTextCount: number;
  averageTextLength: number;
  onSuccess: () => void;
  onCancel: () => void;
  availableAgents: Agent[];
}

interface FormData {
  agentId: number;
}

const AIJudgeExecutionForm: React.FC<AIJudgeExecutionFormProps> = ({
  contestId,
  contestTextCount,
  averageTextLength,
  onSuccess,
  onCancel,
  availableAgents
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
  
  const [showConfirmation, setShowConfirmation] = useState(false);
  const { user } = useAuthStore();
  const credits = user?.credit_balance || 0;
  
  const { control, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    defaultValues: {
      agentId: availableAgents.length > 0 ? availableAgents[0].id : 0
    }
  });
  
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
  
  const onSubmit = async (data: FormData) => {
    setShowConfirmation(true);
  };
  
  const executeJudge = async (data: FormData) => {
    setIsExecuting(true);
    setError(null);
    setProgress(0);
    
    try {
      const selectedAgent = availableAgents.find(agent => agent.id === data.agentId);
      
      if (!selectedAgent) {
        throw new Error('Selected agent not found');
      }
      
      await executeJudgeAgent({
        agent_id: data.agentId,
        model: selectedAgent.model,
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
      setError(err.message || 'Failed to execute AI judge. Please try again.');
      setIsExecuting(false);
    }
  };
  
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-bold mb-4">Execute AI Judge</h2>
      
      {error && (
        <div className="bg-red-50 text-red-700 p-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Select AI Judge
          </label>
          <Controller
            name="agentId"
            control={control}
            rules={{ required: "Please select an AI judge" }}
            render={({ field }) => (
              <select 
                {...field} 
                disabled={isExecuting}
                onChange={e => field.onChange(Number(e.target.value))}
                className="w-full px-3 py-2 border rounded-lg"
              >
                {availableAgents.map(agent => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name} ({agent.model})
                  </option>
                ))}
                {availableAgents.length === 0 && (
                  <option disabled value={0}>No AI judges available</option>
                )}
              </select>
            )}
          />
          {errors.agentId && (
            <p className="text-red-600 text-sm mt-1">{errors.agentId.message}</p>
          )}
        </div>
        
        <div className="bg-blue-50 p-4 rounded-lg mb-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-blue-800 font-medium">Estimated Credit Cost:</p>
              <p className="text-xs text-blue-600">
                Fixed cost per contest evaluation
              </p>
            </div>
            <div className="text-blue-800 font-bold text-xl">
              {estimatedCost !== null ? estimatedCost : 10} credits
            </div>
          </div>
          <p className="text-xs text-blue-700 mt-2">
            <strong>Note:</strong> The AI judge will evaluate all submissions in the contest.
            This operation cannot be undone once started.
          </p>
        </div>
        
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-600">
            Available Credits: <span className="font-medium">{credits}</span>
          </div>
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border rounded-lg hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isExecuting || availableAgents.length === 0 || credits < (estimatedCost || 0)}
              className={`px-4 py-2 rounded-lg font-medium ${
                isExecuting || availableAgents.length === 0 || credits < (estimatedCost || 0)
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-indigo-600 text-white hover:bg-indigo-700'
              }`}
            >
              {isExecuting ? 'Processing...' : 'Execute Judge'}
            </button>
          </div>
        </div>
      </form>
      
      {/* Confirmation Modal */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-bold mb-4">Confirm AI Judge Execution</h3>
            <p className="mb-4">
              You are about to use <span className="font-bold">{estimatedCost !== null ? estimatedCost : 10} credits</span> to evaluate all submissions in this contest using an AI judge.
            </p>
            <p className="text-amber-600 text-sm mb-4">
              <strong>Warning:</strong> This action cannot be undone. The AI judge will evaluate all submissions and the results will be immediately visible to participants.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowConfirmation(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={() => executeJudge(watch())}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Confirm & Execute
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIJudgeExecutionForm; 