import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { getAgentsWithPagination, Agent, updateAgent, deleteAgent } from '../../services/agentService';
import { User } from '../../services/userService';
import BackButton from '../../components/ui/BackButton';
import AgentFormModal from '../../components/Agent/AgentFormModal';
import Pagination from '../../components/shared/Pagination';
import AdminUserSearch from '../../components/shared/AdminUserSearch';

const AdminAgentsPage: React.FC = () => {
  // Data state
  const [displayedAgents, setDisplayedAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(25);
  
  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isUserFilterActive, setIsUserFilterActive] = useState(false);
  
  // Modal state
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  
  // Fetch agents with current filters and pagination
    const fetchAgents = async () => {
      setIsLoading(true);
      try {
      const skip = (currentPage - 1) * itemsPerPage;
      const agents = await getAgentsWithPagination(
        skip,
        itemsPerPage,
        searchQuery.trim() || undefined,
        typeFilter !== 'all' ? typeFilter : undefined,
        isUserFilterActive && selectedUser ? selectedUser.id : undefined
      );
      setDisplayedAgents(agents);
      // Note: For now we'll estimate total count since backend doesn't return it
      // In a production app, we'd modify the backend to return total count
      setTotalCount(agents.length === itemsPerPage ? (currentPage * itemsPerPage) + 1 : skip + agents.length);
      } catch (error) {
        console.error('Error fetching agents:', error);
        toast.error('Failed to load AI agents');
      } finally {
        setIsLoading(false);
      }
    };

  // Fetch agents whenever filters or pagination change
  useEffect(() => {
    fetchAgents();
  }, [currentPage, searchQuery, typeFilter, selectedUser, isUserFilterActive]);

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
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setCurrentPage(1);
  };

  const handleTypeFilterChange = (value: string) => {
    setTypeFilter(value);
    setCurrentPage(1);
  };

  // Handle agent update
  const handleUpdateAgent = async (agentData: Partial<Agent>) => {
    if (!selectedAgent) return;
    
    try {
      const apiAgentData = {
        name: agentData.name,
        description: agentData.description,
        type: agentData.type,
        prompt: agentData.prompt,
        is_public: agentData.is_public
      };
      
      await updateAgent(selectedAgent.id, apiAgentData);
      
      // Refresh the current page
      await fetchAgents();
      
      toast.success('Agent updated successfully');
      setIsEditModalOpen(false);
    } catch (error) {
      console.error('Error updating agent:', error);
      toast.error('Failed to update agent');
    }
  };

  // Handle agent deletion
  const handleDeleteAgent = async () => {
    if (!selectedAgent) return;
    
    try {
      await deleteAgent(selectedAgent.id);
      
      // Refresh the current page
      await fetchAgents();
      
      toast.success('Agent deleted successfully');
      setIsDeleteModalOpen(false);
    } catch (error) {
      console.error('Error deleting agent:', error);
      toast.error('Failed to delete agent');
    }
  };

  const openEditModal = (agent: Agent) => {
    setSelectedAgent(agent);
    setIsEditModalOpen(true);
  };

  const openDeleteModal = (agent: Agent) => {
    setSelectedAgent(agent);
    setIsDeleteModalOpen(true);
  };

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center">
          <BackButton to="/admin" label="Back to Dashboard" />
          <h1 className="text-3xl font-bold ml-4">AI Agents Management</h1>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b">
          <div className="flex flex-col lg:flex-row lg:items-end gap-4">
            <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                  Search Agents
              </label>
              <input
                type="text"
                  placeholder="Search by name or description..."
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={searchQuery}
                  onChange={(e) => handleSearchChange(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                  Agent Type
              </label>
              <select
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={typeFilter}
                  onChange={(e) => handleTypeFilterChange(e.target.value)}
              >
                <option value="all">All Types</option>
                <option value="writer">Writers</option>
                <option value="judge">Judges</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                  Filter by Owner
              </label>
                <AdminUserSearch
                  onUserSelect={handleUserSelect}
                  placeholder="Search users..."
                  selectedUser={selectedUser}
                />
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
              Filtering by owner: <span className="font-medium">{selectedUser.username}</span>
            </div>
          )}
          <div className="mt-2 text-sm text-gray-500">
            Showing {displayedAgents.length} agents
          </div>
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
                    Name
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Model
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Owner
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Visibility
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {displayedAgents.length > 0 ? (
                  displayedAgents.map((agent) => {
                    return (
                      <tr key={agent.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="font-medium text-gray-900">{agent.name}</div>
                          <div className="text-sm text-gray-500">
                            {agent.description.length > 50 
                              ? `${agent.description.substring(0, 50)}...` 
                              : agent.description}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            agent.type === 'writer' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                          }`}>
                            {agent.type.charAt(0).toUpperCase() + agent.type.slice(1)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {agent.model}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <div className="font-medium text-gray-900">
                            Owner ID: {agent.owner_id}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            agent.is_public ? 'bg-green-100 text-green-800' : 'bg-purple-100 text-purple-800'
                          }`}>
                            {agent.is_public ? 'Public' : 'Private'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(agent.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                          <div className="flex justify-center space-x-2">
                            <button
                              onClick={() => openEditModal(agent)}
                              className="text-indigo-600 hover:text-indigo-900"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => openDeleteModal(agent)}
                              className="text-red-600 hover:text-red-900"
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                      No agents found matching your criteria.
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

      {/* Edit Modal */}
      {selectedAgent && (
        <AgentFormModal
          isOpen={isEditModalOpen}
          onClose={() => setIsEditModalOpen(false)}
          onSubmit={(agentData) => {
            // Convert AgentFormModal format to updateAgent format
            handleUpdateAgent({
              ...selectedAgent,
              name: agentData.name,
              description: agentData.description,
              type: agentData.type,
              prompt: agentData.prompt,
              is_public: agentData.is_public
            });
          }}
          initialAgent={{
            name: selectedAgent.name,
            description: selectedAgent.description,
            type: selectedAgent.type as 'writer' | 'judge',
            prompt: selectedAgent.prompt,
            is_public: selectedAgent.is_public
          }}
          isEditing={true}
          isAdmin={true}
        />
      )}

      {/* Delete Modal */}
      {isDeleteModalOpen && selectedAgent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-bold mb-4">Delete AI Agent</h3>
            <p className="mb-4">
              Are you sure you want to delete the agent <span className="font-bold">{selectedAgent.name}</span>?
              This action cannot be undone.
            </p>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setIsDeleteModalOpen(false)}
                className="px-4 py-2 border rounded-md hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAgent}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                Delete Agent
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminAgentsPage; 