import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { executeWriterAgent, estimateWriterCost, Agent } from '../../services/agentService';
import { getModels, LLMModel } from '../../services/modelService';
import { useAuthStore } from '../../store/authStore';

interface AIWriterExecutionFormProps {
  onSuccess: (textId: number) => void;
  availableAgents: Agent[];
}

interface FormData {
  agentId: number;
  modelId: string;
  prompt: string;
  title: string;
  contestDescription?: string;
}

const AIWriterExecutionForm: React.FC<AIWriterExecutionFormProps> = ({ 
  onSuccess,
  availableAgents
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [pendingFormData, setPendingFormData] = useState<FormData | null>(null);
  const [estimatedCost, setEstimatedCost] = useState(0);
  const [isEstimatingCost, setIsEstimatingCost] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<LLMModel[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const { user } = useAuthStore();
  const credits = user?.credits || 0;

  const { control, handleSubmit, watch, setValue, formState: { errors } } = useForm<FormData>({
    defaultValues: {
      agentId: availableAgents.length > 0 ? availableAgents[0].id : 0,
      modelId: '',
      prompt: '',
      title: '',
      contestDescription: ''
    }
  });

  const selectedAgentId = watch('agentId');
  const selectedModelId = watch('modelId');
  const prompt = watch('prompt');
  const title = watch('title');
  const contestDescription = watch('contestDescription');
  
  // Load available models
  useEffect(() => {
    const fetchModels = async () => {
      try {
        setLoadingModels(true);
        const modelsResponse = await getModels();
        setModels(modelsResponse);
        
        // Set default model if available and no model is currently selected
        if (modelsResponse.length > 0 && !selectedModelId) {
          setValue('modelId', modelsResponse[0].id);
        }
        setLoadingModels(false);
      } catch (err) {
        console.error('Error fetching models:', err);
        setError('Failed to load models. Please try again.');
        setLoadingModels(false);
      }
    };
    
    fetchModels();
  }, [setValue]);
  
  // Track when user is typing
  useEffect(() => {
    setIsTyping(true);
    
    // Clear typing state after a short delay
    const typingTimeoutId = setTimeout(() => {
      setIsTyping(false);
    }, 500);
    
    return () => clearTimeout(typingTimeoutId);
  }, [prompt, title, contestDescription]);
  
  // Calculate estimated cost using backend endpoint with debouncing
  useEffect(() => {
    const estimateCost = async () => {
      if (!prompt || !title || selectedAgentId === 0 || !selectedModelId) {
        setEstimatedCost(0);
        return;
      }
      
      setIsEstimatingCost(true);
      try {
        const costEstimate = await estimateWriterCost({
          agent_id: selectedAgentId,
          model: selectedModelId,
          title,
          description: prompt,
          contest_description: contestDescription || undefined
        });
        setEstimatedCost(costEstimate.estimated_credits);
      } catch (err) {
        console.error('Cost estimation error:', err);
        setEstimatedCost(0);
      } finally {
        setIsEstimatingCost(false);
      }
    };

    // Debounce the cost estimation - wait 1 second after user stops typing
    const timeoutId = setTimeout(estimateCost, 1000);
    
    // Cleanup timeout if dependencies change before timeout completes
    return () => clearTimeout(timeoutId);
  }, [prompt, title, selectedAgentId, selectedModelId, contestDescription]);
  
  const onSubmit = async (data: FormData) => {
    setPendingFormData(data);
    setShowConfirmation(true);
  };
  
  const executeAIWriter = async (data: FormData) => {
    setIsSubmitting(true);
    setError(null);
    
    try {
      const selectedAgentObject = availableAgents.find(agent => agent.id === data.agentId);
      
      if (!selectedAgentObject) {
        throw new Error('Selected agent not found');
      }
      
      // Build the request payload, filtering out empty values
      const requestPayload: any = {
        agent_id: data.agentId,
        model: data.modelId,
        title: data.title,
        description: data.prompt
      };
      
      // Only include contest_description if it has content
      if (data.contestDescription && data.contestDescription.trim()) {
        requestPayload.contest_description = data.contestDescription.trim();
      }
      
      console.log('Sending writer execution request:', requestPayload);
      
      const result = await executeWriterAgent(requestPayload);
      
      if (result.result_id) {
        onSuccess(result.result_id);
      } else {
        throw new Error('No text ID returned from the API');
      }
    } catch (err: any) {
      console.error('Error executing AI writer:', err);
      
      // Handle different types of errors
      let errorMessage = 'Failed to execute AI writer. Please try again.';
      
      if (err.response?.status === 422) {
        // Validation error
        const validationErrors = err.response?.data?.detail;
        if (Array.isArray(validationErrors)) {
          errorMessage = `Validation error: ${validationErrors.map((e: any) => e.msg).join(', ')}`;
        } else if (typeof validationErrors === 'string') {
          errorMessage = `Validation error: ${validationErrors}`;
        } else {
          errorMessage = 'Invalid request data. Please check your input.';
        }
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
      setShowConfirmation(false);
      setPendingFormData(null);
    }
  };
  
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-bold mb-4">Generate Text with AI Writer</h2>
      
      {error && (
        <div className="bg-red-50 text-red-700 p-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            AI Writer Agent
          </label>
          <Controller
            name="agentId"
            control={control}
            rules={{ required: "Please select an AI writer agent" }}
            render={({ field }) => (
              <select 
                {...field} 
                disabled={isSubmitting}
                onChange={e => field.onChange(Number(e.target.value))}
                className="w-full px-3 py-2 border rounded-lg"
              >
                {availableAgents.map(agent => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name}
                  </option>
                ))}
                {availableAgents.length === 0 && (
                  <option disabled value={0}>No AI agents available</option>
                )}
              </select>
            )}
          />
          {errors.agentId && (
            <p className="text-red-600 text-sm mt-1">{errors.agentId.message}</p>
          )}
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            AI Model
          </label>
          <Controller
            name="modelId"
            control={control}
            rules={{ required: "Please select an AI model" }}
            render={({ field }) => (
              <select 
                {...field} 
                disabled={isSubmitting || loadingModels}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="">
                  {loadingModels ? "Loading models..." : "-- Select an AI model --"}
                </option>
                {models.map(model => (
                  <option key={model.id} value={model.id}>
                    {model.name} ({model.provider})
                  </option>
                ))}
              </select>
            )}
          />
          {errors.modelId && (
            <p className="text-red-600 text-sm mt-1">{errors.modelId.message}</p>
          )}
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Title
          </label>
          <Controller
            name="title"
            control={control}
            rules={{ required: "Title is required" }}
            render={({ field }) => (
              <input
                {...field}
                disabled={isSubmitting}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="Enter a title for the generated text"
              />
            )}
          />
          {errors.title && (
            <p className="text-red-600 text-sm mt-1">{errors.title.message}</p>
          )}
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Prompt for AI Writer
          </label>
          <Controller
            name="prompt"
            control={control}
            rules={{ 
              required: "Prompt is required",
              minLength: {
                value: 20,
                message: "Prompt should be at least 20 characters"
              }
            }}
            render={({ field }) => (
              <textarea
                {...field}
                disabled={isSubmitting}
                rows={6}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="Enter detailed instructions for the AI writer..."
              />
            )}
          />
          {errors.prompt && (
            <p className="text-red-600 text-sm mt-1">{errors.prompt.message}</p>
          )}
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Contest Context (Optional)
          </label>
          <Controller
            name="contestDescription"
            control={control}
            render={({ field }) => (
              <textarea
                {...field}
                disabled={isSubmitting}
                rows={3}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="Optional: Provide contest context to help the AI understand the specific requirements..."
              />
            )}
          />
        </div>
        
        <div className="bg-blue-50 p-4 rounded-lg mb-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-blue-800 font-medium">Estimated Credit Cost:</p>
              <div className="flex items-center space-x-2 text-xs text-blue-600 mt-1">
                {isTyping ? (
                  <>
                    <div className="flex items-center space-x-1">
                      <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse"></div>
                      <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                      <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                    </div>
                    <span className="text-blue-500 italic">Waiting for you to finish typing...</span>
                  </>
                ) : isEstimatingCost ? (
                  <>
                    <div className="animate-spin h-3 w-3 border border-blue-400 border-t-transparent rounded-full"></div>
                    <span>Calculating based on your input...</span>
                  </>
                ) : (
                  <span>Based on your input and selected AI model</span>
                )}
              </div>
            </div>
            <div className="text-blue-800 font-bold text-xl">
              {isEstimatingCost ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin h-5 w-5 border-2 border-blue-800 border-t-transparent rounded-full"></div>
                  <span>Calculating...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <span>{estimatedCost} credits</span>
                  {isTyping && (
                    <div className="px-2 py-1 bg-blue-200 text-blue-700 text-xs rounded-full font-medium">
                      Will update soon
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
          <p className="text-xs text-blue-700 mt-2">
            <strong>Note:</strong> This estimate updates automatically as you type. Actual credit usage may vary based on the final generated content length and complexity.
          </p>
        </div>
        
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-600">
            Available Credits: <span className="font-medium">{credits}</span>
          </div>
          <button
            type="submit"
            disabled={isSubmitting || availableAgents.length === 0 || models.length === 0 || !selectedModelId || credits < estimatedCost || isEstimatingCost}
            className={`px-4 py-2 rounded-lg font-medium ${
              isSubmitting || availableAgents.length === 0 || models.length === 0 || !selectedModelId || credits < estimatedCost || isEstimatingCost
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-indigo-600 text-white hover:bg-indigo-700'
            }`}
          >
            {isSubmitting ? 'Processing...' : 'Generate Text'}
          </button>
        </div>
      </form>
      
      {/* Confirmation Modal */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-bold mb-4">Confirm AI Text Generation</h3>
            <p className="mb-4">
              You are about to use approximately <span className="font-bold">{estimatedCost} credits</span> to generate a text using an AI writer.
            </p>
            <p className="text-amber-600 text-sm mb-4">
              <strong>Note:</strong> The actual cost may vary slightly based on the complexity and length of the generated content.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowConfirmation(false);
                  setPendingFormData(null);
                }}
                className="px-4 py-2 border rounded-lg hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (pendingFormData) {
                    executeAIWriter(pendingFormData);
                  }
                }}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Confirm & Generate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIWriterExecutionForm; 