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

export interface CreditTransactionWithUser extends CreditTransaction {
  username: string;
  email: string;
}

export interface FilteredSummaryStats {
  total_purchased: number;
  total_consumed: number;
  total_refunded: number;
  total_adjusted: number;
  total_cost_usd: number;
  total_transactions: number;
}

// Get credit transactions for the current user
export const getUserCreditTransactions = async (): Promise<CreditTransaction[]> => {
  const response = await apiClient.get('/users/me/credits/transactions');
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
  user_id?: number,
  transaction_type?: string,
  ai_model?: string,
  date_from?: string,
  date_to?: string
): Promise<CreditTransactionWithUser[]> => {
  const params: any = { skip, limit };
  if (user_id) params.user_id = user_id;
  if (transaction_type) params.transaction_type = transaction_type;
  if (ai_model) params.ai_model = ai_model;
  if (date_from) params.date_from = date_from;
  if (date_to) params.date_to = date_to;

  const response = await apiClient.get('/admin/credits/transactions-with-users', { params });
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

export const getCreditTransactions = async (
  skip: number = 0,
  limit: number = 100,
  filters: {
    user_id?: number;
    transaction_type?: string;
    ai_model?: string;
    date_from?: string;
    date_to?: string;
  } = {}
): Promise<CreditTransaction[]> => {
  const params: any = { skip, limit };
  if (filters.user_id) params.user_id = filters.user_id;
  if (filters.transaction_type) params.transaction_type = filters.transaction_type;
  if (filters.ai_model) params.ai_model = filters.ai_model;
  if (filters.date_from) params.date_from = filters.date_from;
  if (filters.date_to) params.date_to = filters.date_to;

  const response = await apiClient.get('/admin/credits/transactions', { params });
  return response.data;
};

// Admin: Get filtered summary statistics
export const getFilteredSummaryStats = async (
  user_id?: number,
  transaction_type?: string,
  ai_model?: string,
  date_from?: string,
  date_to?: string
): Promise<FilteredSummaryStats> => {
  const params: any = {};
  if (user_id) params.user_id = user_id;
  if (transaction_type) params.transaction_type = transaction_type;
  if (ai_model) params.ai_model = ai_model;
  if (date_from) params.date_from = date_from;
  if (date_to) params.date_to = date_to;

  const response = await apiClient.get('/admin/credits/summary-stats', { params });
  return response.data;
}; 