import apiClient from '../utils/apiClient';

export interface Agent {
  id: number;
  name: string;
  description: string;
  type: 'writer' | 'judge';
  prompt: string;
  model: string;
  owner_id: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  version: string;
}

export interface CreateAgentRequest {
  name: string;
  description: string;
  type: 'writer' | 'judge';
  prompt: string;
  is_public?: boolean;
}

export interface UpdateAgentRequest {
  name?: string;
  description?: string;
  prompt?: string;
  is_public?: boolean;
}

export interface AgentExecution {
  id: number;
  agent_id: number;
  user_id: number;
  owner_id: number;
  execution_type: 'judge' | 'writer';
  contest_id?: number;
  text_id?: number;
  created_at: string;
  credits_used: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result_id?: number;
}

export interface AgentExecuteJudgeRequest {
  agent_id: number;
  model: string;
  contest_id: number;
}

export interface AgentExecuteWriterRequest {
  agent_id: number;
  model: string;
  title?: string;
  description?: string;
  contest_description?: string;
}

export interface WriterCostEstimate {
  estimated_credits: number;
  estimated_input_tokens: number;
  estimated_output_tokens: number;
}

export interface JudgeCostEstimateRequest {
  agent_id: number;
  model: string;
  contest_id: number;
}

export interface JudgeCostEstimate {
  estimated_credits: number;
  estimated_input_tokens: number;
  estimated_output_tokens: number;
}

// Function to get agents
export const getAgents = async (publicOnly?: boolean, skip: number = 0, limit: number = 100): Promise<Agent[]> => {
  const params: any = { skip, limit };
  if (publicOnly !== undefined) {
    params.public = publicOnly;
  }
  
  const response = await apiClient.get('/agents/', { params });
  return response.data;
};

// Admin: Get agents with pagination and search
export const getAgentsWithPagination = async (
  skip: number = 0,
  limit: number = 25,
  search?: string,
  type?: string,
  owner_id?: number
): Promise<Agent[]> => {
  const params: any = { skip, limit };
  if (search) params.search = search;
  if (type && type !== 'all') params.type = type;
  if (owner_id) params.owner_id = owner_id;
  
  const response = await apiClient.get('/agents', { params });
  return response.data;
};

// Get a specific agent by ID
export const getAgent = async (id: number): Promise<Agent> => {
  const response = await apiClient.get(`/agents/${id}`);
  return response.data;
};

// Create a new agent
export const createAgent = async (agentData: CreateAgentRequest): Promise<Agent> => {
  const response = await apiClient.post('/agents', agentData);
  return response.data;
};

// Update an existing agent
export const updateAgent = async (id: number, agentData: UpdateAgentRequest): Promise<Agent> => {
  const response = await apiClient.put(`/agents/${id}`, agentData);
  return response.data;
};

// Delete an agent
export const deleteAgent = async (id: number): Promise<void> => {
  await apiClient.delete(`/agents/${id}`);
};

// Clone a public agent
export const cloneAgent = async (id: number): Promise<Agent> => {
  const response = await apiClient.post(`/agents/${id}/clone`);
  return response.data;
};

// Execute a judge agent on a contest
export const executeJudgeAgent = async (request: AgentExecuteJudgeRequest): Promise<AgentExecution> => {
  const response = await apiClient.post('/agents/execute/judge', request);
  return response.data;
};

// Estimate cost for writer agent execution
export const estimateWriterCost = async (request: AgentExecuteWriterRequest): Promise<WriterCostEstimate> => {
  const response = await apiClient.post('/agents/estimate/writer', request);
  return response.data;
};

// Estimate cost for judge agent execution
export const estimateJudgeCost = async (request: JudgeCostEstimateRequest): Promise<JudgeCostEstimate> => {
  const response = await apiClient.post('/agents/estimate/judge', request);
  return response.data;
};

// Execute a writer agent to generate text
export const executeWriterAgent = async (request: AgentExecuteWriterRequest): Promise<AgentExecution> => {
  const response = await apiClient.post('/agents/execute/writer', request);
  return response.data;
};

// Get agent executions for the current user
export const getAgentExecutions = async (): Promise<AgentExecution[]> => {
  const response = await apiClient.get('/agents/executions');
  return response.data;
}; 