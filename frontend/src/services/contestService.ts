import apiClient from '../utils/apiClient';

export interface Contest {
  id: number;
  title: string;
  description: string;
  creator_id: number;
  created_at: string;
  updated_at: string;
  start_date?: string;
  end_date: string | null;
  is_private: boolean;
  password: string | null;
  status: 'open' | 'evaluation' | 'closed';
  participant_count?: number;
  text_count?: number;
  judge_restrictions: boolean;
  author_restrictions: boolean;
  min_votes_required?: number;
  has_password: boolean;
}

export interface CreateContestRequest {
  title: string;
  description: string;
  is_private: boolean;
  password?: string;
  end_date?: string;
  judge_restrictions?: boolean;
  author_restrictions?: boolean;
  min_votes_required?: number;
}

export interface UpdateContestRequest {
  title?: string;
  description?: string;
  is_private?: boolean;
  password?: string;
  status?: 'open' | 'evaluation' | 'closed';
  end_date?: string;
  judge_restrictions?: boolean;
  author_restrictions?: boolean;
  min_votes_required?: number;
}

// Get all contests
export const getContests = async (): Promise<Contest[]> => {
  const response = await apiClient.get('/contests');
  return response.data;
};

// Get contests created by the current user
export const getUserContests = async (): Promise<Contest[]> => {
  const response = await apiClient.get('/contests', {
    params: { creator: 'me' },
  });
  return response.data;
};

// Get a specific contest by ID
export const getContest = async (id: number, password?: string): Promise<Contest> => {
  const params = password ? { password } : {};
  const response = await apiClient.get(`/contests/${id}`, { params });
  return response.data;
};

// Create a new contest
export const createContest = async (contestData: CreateContestRequest): Promise<Contest> => {
  const response = await apiClient.post('/contests', contestData);
  return response.data;
};

// Update an existing contest
export const updateContest = async (id: number, contestData: UpdateContestRequest): Promise<Contest> => {
  const response = await apiClient.put(`/contests/${id}`, contestData);
  return response.data;
};

// Delete a contest
export const deleteContest = async (id: number): Promise<void> => {
  await apiClient.delete(`/contests/${id}`);
};

// Submit a text to a contest
export const submitTextToContest = async (contestId: number, textId: number, password?: string): Promise<void> => {
  const data = { text_id: textId };
  const params = password ? { password } : {};
  await apiClient.post(`/contests/${contestId}/submissions`, data, { params });
};

// Get all submissions for a contest
export const getContestSubmissions = async (contestId: number, password?: string): Promise<any[]> => {
  const response = await apiClient.get(`/contests/${contestId}/submissions`);
  return response.data;
};

// Remove a submission from a contest
export const removeSubmissionFromContest = async (contestId: number, submissionId: number): Promise<void> => {
  await apiClient.delete(`/contests/${contestId}/submissions/${submissionId}`);
};

// Assign a judge (user or AI agent) to a contest
export const assignJudgeToContest = async (
  contestId: number, 
  userId?: number, 
  agentId?: number
): Promise<any> => {
  if ((!userId && !agentId) || (userId && agentId)) {
    throw new Error('Exactly one of userId or agentId must be provided');
  }
  
  const data = userId ? { user_id: userId } : { agent_id: agentId };
  const response = await apiClient.post(`/contests/${contestId}/judges`, data);
  return response.data;
};

// Get all judges for a contest
export const getContestJudges = async (contestId: number): Promise<any[]> => {
  const response = await apiClient.get(`/contests/${contestId}/judges`);
  return response.data;
};

// Remove a judge from a contest
export const removeJudgeFromContest = async (contestId: number, judgeId: number): Promise<void> => {
  await apiClient.delete(`/contests/${contestId}/judges/${judgeId}`);
}; 