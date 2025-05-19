import apiClient from '../utils/apiClient';
import { User } from '../types/auth';
import { Contest } from './contestService';

export interface DashboardData {
  user_info: User;
  author_contests: Contest[];
  judge_contests: Contest[];
  credit_balance?: number;
  urgent_actions?: {
    type: 'judge_contest' | 'evaluate_contest';
    contest_id: number;
    contest_title: string;
    count?: number;
  }[];
  contest_count?: number;
  text_count?: number;
  agent_count?: number;
  participation?: {
    as_author: number;
    as_judge: number;
  };
}

// Get dashboard data for the current user
export const getDashboardData = async (): Promise<DashboardData> => {
  const response = await apiClient.get('/dashboard');
  return response.data;
};

// Get participation data for the current user
export const getUserParticipation = async (): Promise<any> => {
  // This endpoint might be part of the dashboard endpoint or a separate one
  // For now, we'll assume it's included in the dashboard data
  const dashboardData = await getDashboardData();
  return {
    asAuthor: dashboardData.participation?.as_author || 0,
    asJudge: dashboardData.participation?.as_judge || 0
  };
}; 