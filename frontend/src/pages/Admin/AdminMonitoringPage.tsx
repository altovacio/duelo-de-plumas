import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import BackButton from '../../components/ui/BackButton';
import { getCreditsTransactionsWithPagination, type CreditTransaction } from '../../services/creditService';
import { User } from '../../services/userService';
import Pagination from '../../components/shared/Pagination';
import AdminUserSearch from '../../components/shared/AdminUserSearch';

const AdminMonitoringPage: React.FC = () => {
  // Data state
  const [displayedTransactions, setDisplayedTransactions] = useState<CreditTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(25);
  
  // Filter state
  const [dateFilter, setDateFilter] = useState<string>('all');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isUserFilterActive, setIsUserFilterActive] = useState(false);
  const [transactionTypeFilter, setTransactionTypeFilter] = useState<string>('all');
  const [modelFilter, setModelFilter] = useState<string>('all');
  const [uniqueModels, setUniqueModels] = useState<string[]>([]);

  // Fetch transactions with current filters and pagination
  const fetchTransactions = async () => {
    setIsLoading(true);
    try {
      const skip = (currentPage - 1) * itemsPerPage;
      
      // Calculate date range for filtering
      let dateFrom: string | undefined;
      if (dateFilter === 'last7days') {
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
        dateFrom = sevenDaysAgo.toISOString();
      } else if (dateFilter === 'last30days') {
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        dateFrom = thirtyDaysAgo.toISOString();
      } else if (dateFilter === 'last365days') {
        const yearAgo = new Date();
        yearAgo.setFullYear(yearAgo.getFullYear() - 1);
        dateFrom = yearAgo.toISOString();
      }

      const transactions = await getCreditsTransactionsWithPagination(
        skip,
        itemsPerPage,
        isUserFilterActive && selectedUser ? selectedUser.id : undefined,
        transactionTypeFilter !== 'all' ? transactionTypeFilter : undefined,
        modelFilter !== 'all' ? modelFilter : undefined,
        dateFrom,
        undefined // dateTo
      );
      
      setDisplayedTransactions(transactions);
      // Note: For now we'll estimate total count since backend doesn't return it
      setTotalCount(transactions.length === itemsPerPage ? (currentPage * itemsPerPage) + 1 : skip + transactions.length);

      // Extract unique models for filter dropdown
      const models = Array.from(new Set(transactions.map(t => t.ai_model).filter((model): model is string => Boolean(model))));
      setUniqueModels(models);
    } catch (error) {
      console.error('Error fetching credit data:', error);
      toast.error('Failed to load credit data');
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch transactions whenever filters or pagination change
  useEffect(() => {
    fetchTransactions();
  }, [currentPage, dateFilter, selectedUser, isUserFilterActive, transactionTypeFilter, modelFilter]);

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Handle user selection from search
  const handleUserSelect = (user: User | null) => {
    setSelectedUser(user);
    setIsUserFilterActive(!!user);
    setCurrentPage(1); // Reset to first page when filtering
  };

  // Handle clearing user filter
  const handleClearUserFilter = () => {
    setSelectedUser(null);
    setIsUserFilterActive(false);
    setCurrentPage(1);
  };

  // Handle filter changes with reset to page 1
  const handleDateFilterChange = (value: string) => {
    setDateFilter(value);
    setCurrentPage(1);
  };

  const handleTransactionTypeFilterChange = (value: string) => {
    setTransactionTypeFilter(value);
    setCurrentPage(1);
  };

  const handleModelFilterChange = (value: string) => {
    setModelFilter(value);
    setCurrentPage(1);
  };

  // Calculate filtered summary stats based on currently displayed transactions
  const getFilteredSummary = () => {
    return {
      totalTransactions: displayedTransactions.length,
      totalPurchased: displayedTransactions
        .filter(t => t.transaction_type === 'purchase')
        .reduce((sum, t) => sum + t.amount, 0),
      totalConsumed: Math.abs(displayedTransactions
        .filter(t => t.transaction_type === 'consumption')
        .reduce((sum, t) => sum + t.amount, 0)),
      totalRefunded: displayedTransactions
        .filter(t => t.transaction_type === 'refund')
        .reduce((sum, t) => sum + t.amount, 0),
      totalAdjusted: displayedTransactions
        .filter(t => t.transaction_type === 'admin_adjustment')
        .reduce((sum, t) => sum + t.amount, 0),
      totalCostUSD: displayedTransactions
        .reduce((sum, t) => sum + (t.real_cost_usd || 0), 0)
    };
  };

  const filteredSummary = getFilteredSummary();

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center">
          <BackButton to="/admin" label="Back to Dashboard" />
          <h1 className="text-3xl font-bold ml-4">Credit Monitoring</h1>
        </div>
      </div>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Total Purchased</h2>
          <p className="text-3xl font-bold text-green-600">{filteredSummary.totalPurchased.toLocaleString()}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Total Consumed</h2>
          <p className="text-3xl font-bold text-red-600">{filteredSummary.totalConsumed.toLocaleString()}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Total Refunded</h2>
          <p className="text-3xl font-bold text-blue-600">{filteredSummary.totalRefunded.toLocaleString()}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Admin Adjusted</h2>
          <p className="text-3xl font-bold text-purple-600">{filteredSummary.totalAdjusted.toLocaleString()}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Total AI Cost (USD)</h2>
          <p className="text-3xl font-bold text-gray-600">${filteredSummary.totalCostUSD.toFixed(4)}</p>
        </div>
      </div>
      
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Filters</h2>
        <div className="flex flex-col lg:flex-row lg:items-end gap-4">
          <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Date Range</label>
              <select
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={dateFilter}
                onChange={(e) => {
                  handleDateFilterChange(e.target.value);
                }}
              >
                <option value="all">All Time</option>
                <option value="last7days">Last 7 Days</option>
                <option value="last30days">Last 30 Days</option>
                <option value="last365days">Last Year</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Filter by User</label>
              <AdminUserSearch
                onUserSelect={handleUserSelect}
                placeholder="Search users..."
                selectedUser={selectedUser}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Transaction Type</label>
              <select
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={transactionTypeFilter}
                onChange={(e) => {
                  handleTransactionTypeFilterChange(e.target.value);
                }}
              >
                <option value="all">All Types</option>
                <option value="purchase">Purchase</option>
                <option value="consumption">Consumption</option>
                <option value="refund">Refund</option>
                <option value="admin_adjustment">Admin Adjustment</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">AI Model</label>
              <select
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={modelFilter}
                onChange={(e) => {
                  handleModelFilterChange(e.target.value);
                }}
              >
                <option value="all">All Models</option>
                {uniqueModels.map(model => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>
            </div>
          </div>
          {isUserFilterActive && (
            <button
              onClick={handleClearUserFilter}
              className="px-3 py-2 text-sm bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200 whitespace-nowrap"
            >
              Clear User Filter
            </button>
          )}
        </div>
        {isUserFilterActive && selectedUser && (
          <div className="mt-2 text-sm text-gray-600">
            Filtering by user: <span className="font-medium">{selectedUser.username}</span>
          </div>
        )}
        <div className="mt-2 text-sm text-gray-500">
          Showing {displayedTransactions.length} of {totalCount} transactions
        </div>
      </div>
      
      {/* Credit Transaction Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold">Transaction History</h2>
        </div>
        
        {isLoading ? (
          <div className="flex justify-center items-center h-32">
            <svg className="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    AI Model
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tokens
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cost (USD)
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {displayedTransactions.length > 0 ? (
                  displayedTransactions.map((transaction) => (
                    <tr key={transaction.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="font-medium text-gray-900">
                          User ID: {transaction.user_id}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          transaction.transaction_type === 'purchase' ? 'bg-green-100 text-green-800' :
                          transaction.transaction_type === 'consumption' ? 'bg-red-100 text-red-800' :
                          transaction.transaction_type === 'refund' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
                        }`}>
                          {transaction.transaction_type === 'purchase' ? 'Purchase' :
                          transaction.transaction_type === 'consumption' ? 'Consumption' :
                          transaction.transaction_type === 'refund' ? 'Refund' : 'Admin Adjustment'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <span className={transaction.amount >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {transaction.amount >= 0 ? '+' : ''}{transaction.amount}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                        {transaction.description}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {transaction.ai_model || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {transaction.tokens_used ? transaction.tokens_used.toLocaleString() : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-medium">
                        ${transaction.real_cost_usd?.toFixed(4) || '0.0000'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(transaction.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                      No transactions found matching your criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
        
        {/* Pagination */}
        {!isLoading && totalCount > itemsPerPage && (
          <Pagination
            currentPage={currentPage}
            totalItems={totalCount}
            itemsPerPage={itemsPerPage}
            onPageChange={handlePageChange}
          />
        )}
      </div>
    </div>
  );
};

export default AdminMonitoringPage; 