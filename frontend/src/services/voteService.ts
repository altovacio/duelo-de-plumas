import apiClient from '../utils/apiClient';

export interface Vote {
  id: number;
  contest_id: number;
  text_id: number;
  contest_judge_id: number;
  agent_execution_id?: number;
  text_place: 1 | 2 | 3 | null;
  comment: string;
  created_at: string;
  
  // Computed properties from backend
  judge_id?: number;
  is_ai_vote: boolean;
  ai_model?: string;
  ai_version?: string;
}

export interface CreateVoteRequest {
  text_id: number;
  text_place: 1 | 2 | 3 | null;
  comment: string;
  is_ai_vote?: boolean;
  ai_model?: string;
}

// Submit multiple votes in a contest (complete judging session)
export const submitVotes = async (
  contestId: number,
  votesData: CreateVoteRequest[]
): Promise<Vote[]> => {
  const response = await apiClient.post(`/contests/${contestId}/votes`, votesData);
  return response.data;
};

// Submit single vote (convenience method - wraps in array)
export const submitVote = async (
  contestId: number,
  voteData: CreateVoteRequest
): Promise<Vote> => {
  const response = await apiClient.post(`/contests/${contestId}/votes`, [voteData]);
  return response.data[0]; // Return first (and only) vote from the array
};

// Get all votes for a contest
export const getContestVotes = async (contestId: number): Promise<Vote[]> => {
  const response = await apiClient.get(`/contests/${contestId}/votes`);
  return response.data;
};

// Get votes by a specific judge in a contest
export const getJudgeVotes = async (
  contestId: number,
  judgeId: number,
  voteType?: 'human' | 'ai'
): Promise<Vote[]> => {
  const params = voteType ? { vote_type: voteType } : {};
  const response = await apiClient.get(`/contests/${contestId}/votes/${judgeId}`, { params });
  return response.data;
};

// Delete a vote
export const deleteVote = async (voteId: number): Promise<void> => {
  await apiClient.delete(`/votes/${voteId}`);
}; 