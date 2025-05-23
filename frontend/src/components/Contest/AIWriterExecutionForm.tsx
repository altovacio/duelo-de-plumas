import React, { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { executeWriterAgent, Agent } from '../../services/agentService';
import { useAuthStore } from '../../store/authStore';

interface AIWriterExecutionFormProps {
  onSuccess: (textId: number) => void;
  availableAgents: Agent[];
}

interface FormData {
  agentId: number;
  prompt: string;
  title: string;
}

const AIWriterExecutionForm: React.FC<AIWriterExecutionFormProps> = ({ 
  onSuccess,
  availableAgents
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [estimatedCost, setEstimatedCost] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuthStore();
  const credits = user?.credits || 0;

  const { control, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    defaultValues: {
      agentId: availableAgents.length > 0 ? availableAgents[0].id : 0,
      prompt: '',
      title: ''
    }
  });

  const selectedAgent = watch('agentId');
  const prompt = watch('prompt');
  
  // Calculate estimated cost (simplified version)
  React.useEffect(() => {
    if (!prompt) {
      setEstimatedCost(0);
      return;
    }
    
    // This is a placeholder for the actual cost calculation
    // In a real implementation, this might be fetched from an API
    const baseCost = 5; // Base cost in credits
    const costPerChar = 0.01; // Cost per character
    const estimatedTotal = baseCost + (prompt.length * costPerChar);
    
    setEstimatedCost(Math.round(estimatedTotal * 100) / 100);
  }, [prompt, selectedAgent]);
  
  const onSubmit = async (data: FormData) => {
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
      
      const result = await executeWriterAgent({
        agent_id: data.agentId,
        model: selectedAgentObject.model,
        title: data.title,
        description: data.prompt
      });
      
      if (result.text_id) {
        onSuccess(result.text_id);
      } else {
        throw new Error('No text ID returned from the API');
      }
    } catch (err: any) {
      console.error('Error executing AI writer:', err);
      setError(err.message || 'Failed to execute AI writer. Please try again.');
    } finally {
      setIsSubmitting(false);
      setShowConfirmation(false);
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
        
        <div className="bg-blue-50 p-4 rounded-lg mb-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-blue-800 font-medium">Estimated Credit Cost:</p>
              <p className="text-xs text-blue-600">
                Based on prompt length and AI model
              </p>
            </div>
            <div className="text-blue-800 font-bold text-xl">
              {estimatedCost} credits
            </div>
          </div>
          <p className="text-xs text-blue-700 mt-2">
            <strong>Note:</strong> Actual credit usage may vary based on the final generated content. 
            Writer credits can be very variable depending on the complexity of the prompt and the AI model used.
          </p>
        </div>
        
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-600">
            Available Credits: <span className="font-medium">{credits}</span>
          </div>
          <button
            type="submit"
            disabled={isSubmitting || availableAgents.length === 0 || credits < estimatedCost}
            className={`px-4 py-2 rounded-lg font-medium ${
              isSubmitting || availableAgents.length === 0 || credits < estimatedCost
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
              You are about to use <span className="font-bold">{estimatedCost} credits</span> to generate a text using an AI writer.
            </p>
            <p className="text-amber-600 text-sm mb-4">
              <strong>Warning:</strong> Writer credits can be very variable depending on the complexity of the prompt and length of the output.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowConfirmation(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={() => executeAIWriter(watch())}
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