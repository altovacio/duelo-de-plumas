import apiClient from '../utils/apiClient';

export interface Vote {
  id: number;
  contest_id: number;
  text_id: number;
  judge_id: number;
  judge_type: 'human' | 'ai';
  place: 1 | 2 | 3 | null;
  comment: string;
  created_at: string;
  updated_at: string;
  agent_id?: number;
}

export interface CreateVoteRequest {
  text_id: number;
  place: 1 | 2 | 3 | null;
  comment: string;
  agent_id?: number;
}

// Create or update a vote in a contest
export const submitVote = async (
  contestId: number,
  voteData: CreateVoteRequest
): Promise<Vote> => {
  const response = await apiClient.post(`/contests/${contestId}/votes`, voteData);
  return response.data;
};

// Get all votes for a contest
export const getContestVotes = async (contestId: number): Promise<Vote[]> => {
  const response = await apiClient.get(`/contests/${contestId}/votes`);
  return response.data;
};

// Get votes by a specific judge in a contest
export const getJudgeVotes = async (
  contestId: number,
  judgeId: number
): Promise<Vote[]> => {
  const response = await apiClient.get(`/contests/${contestId}/votes/${judgeId}`);
  return response.data;
};

// Delete a vote
export const deleteVote = async (voteId: number): Promise<void> => {
  await apiClient.delete(`/votes/${voteId}`);
}; 