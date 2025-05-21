import apiClient from '../utils/apiClient';

// Define a more specific type for Contest if not already globally defined
// This should align with what the backend's ContestResponse schema provides.
export interface Contest {
  id: number;
  title: string;
  description: string;
  creator_id: number;
  creator?: { id: number; username: string }; // Optional, if backend provides it nested
  created_at: string;
  updated_at: string;
  start_date?: string;
  end_date: string | null;
  is_private: boolean;
  password?: string | null; // Should generally not be sent to client unless necessary for a specific action
  has_password: boolean; // Preferred over sending actual password
  status: 'open' | 'evaluation' | 'closed';
  participant_count?: number;
  text_count?: number;
  judge_restrictions: boolean;
  author_restrictions: boolean;
  min_votes_required?: number;
  // include any other fields that are part of the Contest model
}

// Define TextSubmission structure (align with backend's TextSubmissionResponse)
// This is what the frontend expects for userSubmissions. Ensure author is an object.
export interface ContestText {
  id: number; // This is the submission ID (from ContestText model)
  contest_id: number;
  text_id: number;
  submission_date: string;
  title: string;
  content: string; // May not always be needed for list views
  author?: { id: number; username: string; }; // Crucial for identifying user's own submissions
  owner_id?: number; // If distinct from author and relevant
  ranking?: number | null;
  // evaluations?: any[]; // If evaluations are part of this structure
  created_at?: string; // Text original creation (if different from submission_date)
  updated_at?: string; // Text original update
}


// Update the ContestJudge interface to match the actual database structure
export interface ContestJudge {
  id: number;
  contest_id: number;
  user_judge_id?: number;  // For human judges
  agent_judge_id?: number; // For AI judges
  assignment_date: string;
  has_voted?: boolean;

  // Additional fields for display purposes
  user_name?: string;      // Username for human judges  
  user_email?: string;     // Email for human judges
  agent_name?: string;     // Name for AI judges
  ai_model?: string;       // Model info for AI judges
  ai_judge?: boolean;      // Helper to identify AI judges
}

// Get all contests
export const getContests = async (filters: { status?: string; creator?: string }): Promise<Contest[]> => {
  const response = await apiClient.get('/contests/', { params: filters });
  return response.data;
};

// Get contests created by the current user
export const getUserContests = async (): Promise<Contest[]> => {
  const response = await apiClient.get('/contests/', { params: { creator: 'me' } });
  return response.data;
};

// Get a specific contest by ID
export const getContest = async (id: number, password?: string): Promise<Contest> => {
  const params = password ? { password } : {};
  const response = await apiClient.get(`/contests/${id}`, { params });
  return response.data;
};

// Create a new contest
export const createContest = async (contestData: Omit<Contest, 'id' | 'creator_id' | 'created_at' | 'updated_at' | 'participant_count' | 'text_count' | 'has_password'>): Promise<Contest> => {
  const response = await apiClient.post('/contests/', contestData);
  return response.data;
};

// Update a contest
export const updateContest = async (id: number, contestData: Partial<Omit<Contest, 'id' | 'creator_id' | 'created_at' | 'updated_at' | 'participant_count' | 'text_count' | 'has_password'>>): Promise<Contest> => {
  const response = await apiClient.put(`/contests/${id}`, contestData);
  return response.data;
};

// Delete a contest
export const deleteContest = async (id: number): Promise<void> => {
  await apiClient.delete(`/contests/${id}`);
};

// Submit a text to a contest
export const submitTextToContest = async (contestId: number, textId: number, password?: string): Promise<{ submission_id: number, contest_id: number, text_id: number, submission_date: string }> => {
  const payload = { text_id: textId };
  const params = password ? { password } : {};
  const response = await apiClient.post(`/contests/${contestId}/submissions/`, payload, { params });
  return response.data;
};

// Get all submissions for a contest (creator/admin or specific contest states)
export const getContestSubmissions = async (contestId: number, password?: string): Promise<ContestText[]> => {
  const params = password ? { password } : {};
  const response = await apiClient.get(`/contests/${contestId}/submissions/`, { params });
  return response.data;
};

// New service to get only the current user's submissions for a contest
export const getContestMySubmissions = async (contestId: number): Promise<ContestText[]> => {
  const response = await apiClient.get(`/contests/${contestId}/my-submissions/`);
  return response.data;
};

// Remove a submission from a contest
export const removeSubmissionFromContest = async (contestId: number, submissionId: number): Promise<void> => {
  await apiClient.delete(`/contests/${contestId}/submissions/${submissionId}`);
};


// Get judges for a specific contest
export const getContestJudges = async (id: number): Promise<ContestJudge[]> => {
  const response = await apiClient.get(`/contests/${id}/judges`);
  
  // Transform the response to match our frontend model
  // The backend might be returning a different structure 
  return response.data.map((judge: any) => ({
    id: judge.id || 0,
    contest_id: judge.contest_id,
    user_judge_id: judge.user_judge_id,
    agent_judge_id: judge.agent_judge_id,
    assignment_date: judge.assignment_date,
    has_voted: judge.has_voted,
    // Derived properties for UI
    user_name: judge.user_judge_name,
    user_email: judge.user_judge_email,
    agent_name: judge.agent_judge_name,
    ai_model: judge.agent_judge_model,
    ai_judge: judge.agent_judge_id ? true : false
  }));
};

// Assign a judge to a contest
export const assignJudgeToContest = async (
  contestId: number, 
  judgeData: { user_id: number } | { agent_id: number }
): Promise<ContestJudge> => {
  // Map the frontend's user_id/agent_id to the backend's expected structure
  const backendData = 'user_id' in judgeData 
    ? { user_judge_id: judgeData.user_id }
    : { agent_judge_id: judgeData.agent_id };

  const response = await apiClient.post(`/contests/${contestId}/judges`, backendData);
  
  // Transform the response to match our frontend model
  return {
    id: response.data.id || 0,
    contest_id: response.data.contest_id,
    user_judge_id: response.data.user_judge_id,
    agent_judge_id: response.data.agent_judge_id,
    assignment_date: response.data.assignment_date,
    has_voted: response.data.has_voted,
    // Derived fields
    user_name: response.data.user_judge_name,
    user_email: response.data.user_judge_email,
    agent_name: response.data.agent_judge_name,
    ai_model: response.data.agent_judge_model,
    ai_judge: response.data.agent_judge_id ? true : false
  };
};

// Remove a judge from a contest (using the ContestJudge entry ID)
export const removeJudgeFromContest = async (contestId: number, judgeAssignmentId: number): Promise<void> => {
  await apiClient.delete(`/contests/${contestId}/judges/${judgeAssignmentId}`);
};

// Get contests where the current user is participating (as author)
export const getAuthorParticipation = async (): Promise<Contest[]> => {
  // This endpoint should return all contests where the user has submitted texts
  const response = await apiClient.get('/contests/my-submissions/');
  return response.data;
};

// Get contests where the current user is a judge (human or through AI)
export const getJudgeParticipation = async (): Promise<Contest[]> => {
  // Get contests where user is assigned as a judge
  const response = await apiClient.get('/contests/', { params: { judge: 'me' } });
  return response.data;
}; 