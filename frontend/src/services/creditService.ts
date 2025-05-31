import apiClient from '../utils/apiClient';

export interface CreditTransaction {
  id: number;
  user_id: number;
  amount: number;
  transaction_type: 'purchase' | 'consumption' | 'refund' | 'admin_adjustment';
  description: string;
  ai_model?: string;
  tokens_used?: number;
  real_cost_usd?: number;
  created_at: string;
}

export interface CreditUsageSummary {
  total_credits_used: number;
  usage_by_model: Record<string, number>;
  usage_by_user: Record<string, number>;
  average_cost_per_operation: number;
  total_tokens_used: number;
  total_real_cost_usd: number;
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

// Admin: Get credit transactions with pagination
export const getCreditsTransactionsWithPagination = async (
  skip: number = 0,
  limit: number = 25,
  userId?: number,
  transactionType?: string,
  aiModel?: string,
  dateFrom?: string,
  dateTo?: string
): Promise<CreditTransaction[]> => {
  const params: any = { skip, limit };
  if (userId) params.user_id = userId;
  if (transactionType && transactionType !== 'all') params.transaction_type = transactionType;
  if (aiModel && aiModel !== 'all') params.ai_model = aiModel;
  if (dateFrom) params.date_from = dateFrom;
  if (dateTo) params.date_to = dateTo;
  
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
  try {
    await apiClient.patch(`/admin/users/${userId}/credits`, {
      credits: amount,
      description
    });
  } catch (error) {
    console.error("Error updating user credits:", error);
    throw error;
  }
}; 