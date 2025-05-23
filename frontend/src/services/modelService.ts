import apiClient from '../utils/apiClient';

export interface LLMModel {
  id: string;
  name: string;
  provider: string;
  context_window_k: number;
  input_cost_usd_per_1k_tokens: number;
  output_cost_usd_per_1k_tokens: number;
  available: boolean;
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
  const inputCost = (inputTokens / 1000) * model.input_cost_usd_per_1k_tokens;
  
  // Calculate output cost
  const outputTokens = Math.ceil(estimatedOutputLength / 4);
  const outputCost = (outputTokens / 1000) * model.output_cost_usd_per_1k_tokens;
  
  const totalCost = inputCost + outputCost;
  // Convert to credits (1 credit = $0.01) and ensure minimum of 1 credit
  const credits = Math.ceil(totalCost * 100);
  return Math.max(1, credits);
}; 