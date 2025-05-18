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
  model: string;
  is_public?: boolean;
}

export interface UpdateAgentRequest {
  name?: string;
  description?: string;
  prompt?: string;
  model?: string;
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

// Get all agents (public and owned)
export const getAgents = async (publicOnly?: boolean): Promise<Agent[]> => {
  const params = publicOnly !== undefined ? { public: publicOnly } : {};
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