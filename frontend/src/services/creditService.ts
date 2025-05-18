import apiClient from '../utils/apiClient';

export interface CreditTransaction {
  id: number;
  user_id: number;
  amount: number;
  transaction_type: 'purchase' | 'consumption' | 'refund' | 'admin_adjustment';
  description: string;
  related_entity_type?: 'agent' | 'contest' | 'text';
  related_entity_id?: number;
  created_at: string;
}

export interface CreditUsageSummary {
  total_credits_used: number;
  usage_by_user: {
    user_id: number;
    username: string;
    credits_used: number;
  }[];
  usage_by_agent_type: {
    agent_type: string;
    credits_used: number;
  }[];
}

// Get credit transactions for the current user
export const getUserCreditTransactions = async (): Promise<CreditTransaction[]> => {
  const response = await apiClient.get('/dashboard/credits/transactions');
  return response.data;
};

// Admin only: Get all credit transactions with optional filtering
export const getCreditsTransactions = async (
  userId?: number,
  transactionType?: string,
  startDate?: string,
  endDate?: string
): Promise<CreditTransaction[]> => {
  const params: any = {};
  if (userId) params.user_id = userId;
  if (transactionType) params.transaction_type = transactionType;
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  
  const response = await apiClient.get('/admin/credits/transactions', { params });
  return response.data;
};

// Admin only: Get credit usage summary across the system
export const getCreditUsageSummary = async (): Promise<CreditUsageSummary> => {
  const response = await apiClient.get('/admin/credits/usage');
  return response.data;
};

// Admin only: Update user's credits
export const updateUserCredits = async (userId: number, amount: number, description: string): Promise<void> => {
  await apiClient.patch(`/admin/users/${userId}/credits`, {
    amount,
    description
  });
}; 