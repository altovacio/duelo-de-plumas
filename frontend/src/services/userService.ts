import apiClient from '../utils/apiClient';

// Updated User interface for more comprehensive user details, especially for admin views
export interface User {
  id: number;
  username: string;
  email?: string; // Assuming email is available
  is_admin?: boolean;
  credit_balance?: number; // For admin views
  created_at?: string;
  last_seen?: string | null; // For admin views, to be implemented
  contests_created?: number | string; // For admin views, can be N/A when there's an error
  // Add other fields as returned by GET /admin/users
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

// Function for an admin to delete a user
export const deleteUserByAdmin = async (userId: number): Promise<void> => {
  await apiClient.delete(`/users/${userId}`);
  // No explicit return, will resolve to undefined on success or throw an error on failure
};

// Function for an admin to get all users
export const getAdminUsers = async (): Promise<User[]> => {
  const response = await apiClient.get('/users');
  return response.data;
}; 