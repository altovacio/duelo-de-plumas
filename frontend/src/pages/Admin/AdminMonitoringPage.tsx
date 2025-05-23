import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import BackButton from '../../components/ui/BackButton';
import { getCreditUsageSummary, getCreditsTransactions } from '../../services/creditService';

// Interfaces for API data
interface CreditUsage {
  id: number;
  user_id: number;
  username: string;
  agent_type: string;
  model: string;
  credits_used: number;
  real_cost_usd: number;
  execution_date: string;
}

const AdminMonitoringPage: React.FC = () => {
  const [creditUsageData, setCreditUsageData] = useState<CreditUsage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [dateFilter, setDateFilter] = useState<string>('all');
  const [userFilter, setUserFilter] = useState<string>('all');
  const [agentTypeFilter, setAgentTypeFilter] = useState<string>('all');
  const [modelFilter, setModelFilter] = useState<string>('all');
  const [usageSummary, setUsageSummary] = useState<{
    totalCreditsUsed: number;
    totalCostUSD: number;
    avgCreditsPerExecution: number;
    avgCostPerExecution: number;
  }>({
    totalCreditsUsed: 0,
    totalCostUSD: 0,
    avgCreditsPerExecution: 0,
    avgCostPerExecution: 0
  });
  const [availableModels, setAvailableModels] = useState<string[]>([]);

  useEffect(() => {
    const fetchCreditData = async () => {
      setIsLoading(true);
      try {
        // Fetch real credit usage data from the API
        const transactions = await getCreditsTransactions();
        
        // Transform transactions into the format needed for the UI
        const formattedData: CreditUsage[] = transactions
          .filter(txn => txn.transaction_type === 'consumption' || txn.transaction_type === 'admin_adjustment')
          .map(txn => ({
            id: txn.id,
            user_id: txn.user_id,
            username: txn.user_id.toString(), // This will be updated if we add username to the API
            agent_type: txn.related_entity_type || 'unknown',
            model: txn.related_entity_type === 'agent' ? 'AI Agent' : (txn.related_entity_type || 'unknown'),
            credits_used: Math.abs(txn.amount),
            real_cost_usd: 0, // To be populated if available in the API
            execution_date: txn.created_at
          }));
        
        setCreditUsageData(formattedData);

        // Also fetch credit usage summary
        const summary = await getCreditUsageSummary();
        
        // Extract available models from the usage summary
        const models = Object.keys(summary.usage_by_model || {});
        setAvailableModels(models.length > 0 ? models : ['unknown']);
        
        // Update summary data
        setUsageSummary({
          totalCreditsUsed: summary.total_credits_used || 0,
          totalCostUSD: summary.total_real_cost_usd || 0,
          avgCreditsPerExecution: summary.average_cost_per_operation || 0,
          avgCostPerExecution: summary.total_real_cost_usd / (formattedData.length || 1)
        });
      } catch (error) {
        console.error('Error fetching credit usage data:', error);
        toast.error('Failed to load credit usage data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCreditData();
  }, []);

  // Filter credit usage data
  const filteredData = creditUsageData.filter(item => {
    // Date filter
    if (dateFilter === 'last7days') {
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      if (new Date(item.execution_date) < sevenDaysAgo) {
        return false;
      }
    } else if (dateFilter === 'last30days') {
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      if (new Date(item.execution_date) < thirtyDaysAgo) {
        return false;
      }
    } else if (dateFilter === 'last365days') {
      const yearAgo = new Date();
      yearAgo.setFullYear(yearAgo.getFullYear() - 1);
      if (new Date(item.execution_date) < yearAgo) {
        return false;
      }
    }

    // User filter
    if (userFilter !== 'all' && item.user_id !== parseInt(userFilter)) {
      return false;
    }

    // Agent type filter
    if (agentTypeFilter !== 'all' && item.agent_type !== agentTypeFilter) {
      return false;
    }

    // Model filter
    if (modelFilter !== 'all' && item.model !== modelFilter) {
      return false;
    }

    return true;
  });

  // Get unique users
  const uniqueUsers = Array.from(new Set(creditUsageData.map(item => item.user_id)))
    .map(userId => {
      const user = creditUsageData.find(item => item.user_id === userId);
      return {
        id: userId,
        username: user?.username || `User #${userId}`
      };
    });

  // Get unique agent types
  const uniqueAgentTypes = Array.from(new Set(creditUsageData.map(item => item.agent_type)));

  // Get unique models
  const uniqueModels = Array.from(new Set(creditUsageData.map(item => item.model)));

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
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Total Credits Used</h2>
          <p className="text-3xl font-bold text-indigo-600">{usageSummary.totalCreditsUsed.toFixed(2)}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Total Cost (USD)</h2>
          <p className="text-3xl font-bold text-green-600">${usageSummary.totalCostUSD.toFixed(2)}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Total Executions</h2>
          <p className="text-3xl font-bold text-indigo-600">{filteredData.length}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Avg. Credits Per Run</h2>
          <p className="text-3xl font-bold text-indigo-600">{usageSummary.avgCreditsPerExecution.toFixed(2)}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase mb-2">Avg. Cost Per Run</h2>
          <p className="text-3xl font-bold text-green-600">${usageSummary.avgCostPerExecution.toFixed(4)}</p>
        </div>
      </div>
      
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Date Range</label>
            <select
              className="w-full px-3 py-2 border rounded-lg"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
            >
              <option value="all">All Time</option>
              <option value="last7days">Last 7 Days</option>
              <option value="last30days">Last 30 Days</option>
              <option value="last365days">Last Year</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">User</label>
            <select
              className="w-full px-3 py-2 border rounded-lg"
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
            >
              <option value="all">All Users</option>
              {uniqueUsers.map(user => (
                <option key={user.id} value={user.id}>{user.username}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Agent Type</label>
            <select
              className="w-full px-3 py-2 border rounded-lg"
              value={agentTypeFilter}
              onChange={(e) => setAgentTypeFilter(e.target.value)}
            >
              <option value="all">All Types</option>
              {uniqueAgentTypes.map(type => (
                <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
            <select
              className="w-full px-3 py-2 border rounded-lg"
              value={modelFilter}
              onChange={(e) => setModelFilter(e.target.value)}
            >
              <option value="all">All Models</option>
              {uniqueModels.map(model => (
                <option key={model} value={model}>{model}</option>
              ))}
            </select>
          </div>
        </div>
      </div>
      
      {/* Credit Usage Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold">Credit Usage Details</h2>
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
                    Agent Type
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Model
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Credits Used
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
                {filteredData.length > 0 ? (
                  filteredData.map((item) => (
                    <tr key={item.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {item.username}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          item.agent_type === 'writer' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                        }`}>
                          {item.agent_type.charAt(0).toUpperCase() + item.agent_type.slice(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {item.model}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                        {item.credits_used.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-medium">
                        ${item.real_cost_usd.toFixed(4)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(item.execution_date).toLocaleString()}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                      No credit usage data found matching your criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminMonitoringPage; 