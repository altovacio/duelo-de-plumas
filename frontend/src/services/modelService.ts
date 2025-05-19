import apiClient from '../utils/apiClient';

export interface LLMModel {
  id: string;
  name: string;
  provider: string;
  context_window: number;
  pricing: {
    input_tokens: number;  // Price per million tokens
    output_tokens: number; // Price per million tokens
  };
  enabled: boolean;
}

// Get all available LLM models
export const getModels = async (): Promise<LLMModel[]> => {
  const response = await apiClient.get('/models');
  return response.data;
};

// Get a specific LLM model by ID
export const getModel = async (modelId: string): Promise<LLMModel> => {
  const response = await apiClient.get(`/models/${modelId}`);
  return response.data;
};

// Estimate cost for a text generation or judgment
export const estimateCost = (
  model: LLMModel,
  inputLength: number,
  estimatedOutputLength: number = 1000
): number => {
  // Calculate input cost
  const inputTokens = Math.ceil(inputLength / 4); // Rough estimate: 4 chars per token
  const inputCost = (inputTokens / 1000000) * model.pricing.input_tokens;
  
  // Calculate output cost
  const outputTokens = Math.ceil(estimatedOutputLength / 4);
  const outputCost = (outputTokens / 1000000) * model.pricing.output_tokens;
  
  return inputCost + outputCost;
}; 