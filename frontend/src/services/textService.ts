import apiClient from '../utils/apiClient';

export interface Text {
  id: number;
  title: string;
  content: string;
  owner_id: number;
  author: string;
  created_at: string;
  updated_at: string;
}

export interface CreateTextRequest {
  title: string;
  content: string;
  author: string;
}

export interface UpdateTextRequest {
  title?: string;
  content?: string;
  author?: string;
}

// Function to get all texts for the current user
export const getUserTexts = async (skip: number = 0, limit: number = 100, search?: string): Promise<Text[]> => {
  const params: any = { skip, limit };
  if (search && search.trim()) {
    params.search = search.trim();
  }
  
  const response = await apiClient.get('/texts/my', { params });
  return response.data;
};

// Get a specific text by ID
export const getText = async (id: number): Promise<Text> => {
  const response = await apiClient.get(`/texts/${id}`);
  return response.data;
};

// Create a new text
export const createText = async (textData: CreateTextRequest): Promise<Text> => {
  const response = await apiClient.post('/texts', textData);
  return response.data;
};

// Update an existing text
export const updateText = async (id: number, textData: UpdateTextRequest): Promise<Text> => {
  const response = await apiClient.put(`/texts/${id}`, textData);
  return response.data;
};

// Delete a text
export const deleteText = async (id: number): Promise<void> => {
  await apiClient.delete(`/texts/${id}`);
}; 