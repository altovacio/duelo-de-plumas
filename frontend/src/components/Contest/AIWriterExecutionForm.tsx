import React, { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { executeWriterAgent, estimateWriterCost, Agent } from '../../services/agentService';
import { useAuthStore } from '../../store/authStore';

interface AIWriterExecutionFormProps {
  onSuccess: (textId: number) => void;
  availableAgents: Agent[];
}

interface FormData {
  agentId: number;
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
  const { user } = useAuthStore();
  const credits = user?.credits || 0;

  const { control, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    defaultValues: {
      agentId: availableAgents.length > 0 ? availableAgents[0].id : 0,
      prompt: '',
      title: '',
      contestDescription: ''
    }
  });

  const selectedAgentId = watch('agentId');
  const prompt = watch('prompt');
  const title = watch('title');
  const contestDescription = watch('contestDescription');
  
  // Calculate estimated cost using backend endpoint
  React.useEffect(() => {
    const estimateCost = async () => {
      if (!prompt || !title || selectedAgentId === 0) {
        setEstimatedCost(0);
        return;
      }

      const selectedAgent = availableAgents.find(agent => agent.id === selectedAgentId);
      if (!selectedAgent) {
        setEstimatedCost(0);
        return;
      }
      
      setIsEstimatingCost(true);
      try {
        // Build the estimation request payload, filtering out empty values
        const estimationPayload: any = {
          agent_id: selectedAgentId,
          model: selectedAgent.model,
          title: title,
          description: prompt
        };
        
        // Only include contest_description if it has content
        if (contestDescription && contestDescription.trim()) {
          estimationPayload.contest_description = contestDescription.trim();
        }
        
        console.log('Sending cost estimation request:', estimationPayload);
        
        const estimation = await estimateWriterCost(estimationPayload);
        setEstimatedCost(estimation.estimated_credits);
      } catch (err: any) {
        console.error('Error estimating cost:', err);
        
        // Log the specific error details for debugging
        if (err.response?.status === 422) {
          console.error('Validation error in cost estimation:', err.response?.data?.detail);
        }
        
        setEstimatedCost(0);
      } finally {
        setIsEstimatingCost(false);
      }
    };

    // Debounce the cost estimation
    const timeoutId = setTimeout(estimateCost, 500);
    return () => clearTimeout(timeoutId);
  }, [prompt, title, contestDescription, selectedAgentId, availableAgents]);
  
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
        model: selectedAgentObject.model,
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
                    {agent.name} ({agent.model})
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
              <p className="text-xs text-blue-600">
                Based on your input and selected AI model
              </p>
            </div>
            <div className="text-blue-800 font-bold text-xl">
              {isEstimatingCost ? 'Calculating...' : `${estimatedCost} credits`}
            </div>
          </div>
          <p className="text-xs text-blue-700 mt-2">
            <strong>Note:</strong> This is an estimate. Actual credit usage may vary based on the final generated content length and complexity.
          </p>
        </div>
        
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-600">
            Available Credits: <span className="font-medium">{credits}</span>
          </div>
          <button
            type="submit"
            disabled={isSubmitting || availableAgents.length === 0 || credits < estimatedCost || isEstimatingCost}
            className={`px-4 py-2 rounded-lg font-medium ${
              isSubmitting || availableAgents.length === 0 || credits < estimatedCost || isEstimatingCost
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