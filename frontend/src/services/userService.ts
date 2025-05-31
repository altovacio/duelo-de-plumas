import apiClient from '../utils/apiClient';

// Updated User interface for more comprehensive user details, especially for admin views
export interface User {
  id: number;
  username: string;
  email?: string; // Assuming email is available
  is_admin?: boolean;
  credits?: number; // For admin views
  created_at?: string;
  last_login?: string | null; // For admin views - tracks when user last logged in
  contests_created?: number | string; // For admin views, can be N/A when there's an error
  // Add other fields as returned by GET /admin/users
}

// Admin-specific user interface with guaranteed email
export interface AdminUser {
  id: number;
  username: string;
  email: string;
}

// Function to search for users by username or email (works for all users, returns appropriate data based on auth)
export const searchUsers = async (query: string, skip: number = 0, limit: number = 10): Promise<User[]> => {
  const response = await apiClient.get('/users/search', { 
    params: { 
      username: query,
      skip,
      limit 
    } 
  });
  return response.data;
};

// Function to get multiple users by their IDs (admin only) - includes email
export const getUsersByIds = async (userIds: number[]): Promise<AdminUser[]> => {
  if (userIds.length === 0) return [];
  const response = await apiClient.post('/users/by-ids', userIds);
  return response.data;
};

// Function to get the current user's profile
export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get('/users/me');
  return response.data;
};

// Function for an admin to delete a user
export const deleteUserByAdmin = async (userId: number): Promise<void> => {
  await apiClient.delete(`/admin/users/${userId}`);
  // No explicit return, will resolve to undefined on success or throw an error on failure
};

// Function for an admin to get all users with pagination
export const getAdminUsers = async (skip: number = 0, limit: number = 100): Promise<User[]> => {
  const response = await apiClient.get('/admin/users', { 
    params: { skip, limit } 
  });
  return response.data;
};

// Function for an admin to get all users with contest counts (optimized)
export const getAdminUsersWithCounts = async (skip: number = 0, limit: number = 100): Promise<User[]> => {
  const response = await apiClient.get('/admin/users-with-counts', { 
    params: { skip, limit } 
  });
  return response.data;
};

// Keep the old searchAdminUsers for backward compatibility, but it now uses the same endpoint
export const searchAdminUsers = searchUsers;

// Function for an admin to get a single user by ID
export const getAdminUserById = async (userId: number): Promise<User> => {
  const response = await apiClient.get(`/users/${userId}`);
  return response.data;
};

// Update user profile
export const updateUserProfile = async (userData: Partial<User>): Promise<User> => {
  const response = await apiClient.put('/users/me', userData);
  return response.data;
}; 