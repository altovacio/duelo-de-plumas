import apiClient from '../utils/apiClient';

export interface User {
  id: number;
  username: string;
  email?: string;
  is_admin?: boolean;
  created_at?: string;
}

// Function to search for users by username or email
export const searchUsers = async (query: string): Promise<User[]> => {
  const response = await apiClient.get('/users/search', { params: { q: query } });
  return response.data;
};

// Function to get the current user's profile
export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get('/users/me');
  return response.data;
}; 