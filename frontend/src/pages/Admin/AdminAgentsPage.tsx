import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { getAgents, Agent, updateAgent, deleteAgent } from '../../services/agentService';
import { getUsersByIds, AdminUser } from '../../services/userService';
import BackButton from '../../components/ui/BackButton';
import AgentFormModal from '../../components/Agent/AgentFormModal';

const AdminAgentsPage: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [userFilter, setUserFilter] = useState<string>('all');
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  
  // Cache user information
  const [userCache, setUserCache] = useState<Map<number, AdminUser>>(new Map());
  const [uniqueUsers, setUniqueUsers] = useState<AdminUser[]>([]);

  useEffect(() => {
    const fetchAgents = async () => {
      setIsLoading(true);
      try {
        // Get all agents
        const allAgents = await getAgents();
        setAgents(allAgents);
        
        // Get unique user IDs
        const uniqueUserIds = Array.from(new Set(allAgents.map(agent => agent.owner_id)));
        
        // Fetch user information efficiently
        const userInfos = await getUsersByIds(uniqueUserIds);
        
        // Create user cache and unique users list
        const newUserCache = new Map<number, AdminUser>();
        const uniqueUsersList: AdminUser[] = [];
        
        userInfos.forEach(user => {
          newUserCache.set(user.id, user);
          uniqueUsersList.push(user);
        });
        
        // Add fallback for any missing users (though this should be rare now)
        uniqueUserIds.forEach(userId => {
          if (!newUserCache.has(userId)) {
            const fallbackUser: AdminUser = {
              id: userId,
              username: `User #${userId}`,
              email: 'Unknown'
            };
            newUserCache.set(userId, fallbackUser);
            uniqueUsersList.push(fallbackUser);
          }
        });
        
        setUserCache(newUserCache);
        setUniqueUsers(uniqueUsersList);
      } catch (error) {
        console.error('Error fetching agents:', error);
        toast.error('Failed to load AI agents');
      } finally {
        setIsLoading(false);
      }
    };

    fetchAgents();
  }, []);

  // Handle agent update
  const handleUpdateAgent = async (agentData: Partial<Agent>) => {
    if (!selectedAgent) return;
    
    try {
      // Convert the form data format to what the API expects
      const apiAgentData = {
        name: agentData.name,
        description: agentData.description,
        type: agentData.type,
        prompt: agentData.prompt,
        is_public: agentData.is_public
      };
      
      const updatedAgent = await updateAgent(selectedAgent.id, apiAgentData);
      
      // Update local state
      setAgents(agents.map(agent => 
        agent.id === updatedAgent.id ? updatedAgent : agent
      ));
      
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
      
      // Remove the agent from the local state
      setAgents(agents.filter(agent => agent.id !== selectedAgent.id));
      
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

  // Get user info from cache
  const getUserInfo = (userId: number): AdminUser => {
    return userCache.get(userId) || {
      id: userId,
      username: `User #${userId}`,
      email: 'Unknown'
    };
  };

  // Filter agents based on search query, type filter, and user filter
  const filteredAgents = agents.filter(agent => {
    const matchesSearch = 
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.description.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesType = 
      typeFilter === 'all' || 
      (typeFilter === 'writer' && agent.type === 'writer') || 
      (typeFilter === 'judge' && agent.type === 'judge');
    
    const matchesUser =
      userFilter === 'all' ||
      agent.owner_id.toString() === userFilter;
    
    return matchesSearch && matchesType && matchesUser;
  });

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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search
              </label>
              <input
                type="text"
                placeholder="Search agents..."
                className="w-full px-3 py-2 border rounded-lg"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Type
              </label>
              <select
                className="w-full px-3 py-2 border rounded-lg"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <option value="all">All Types</option>
                <option value="writer">Writers</option>
                <option value="judge">Judges</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Owner
              </label>
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
                {filteredAgents.length > 0 ? (
                  filteredAgents.map((agent) => {
                    const userInfo = getUserInfo(agent.owner_id);
                    return (
                      <tr key={agent.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="font-medium text-gray-900">{agent.name}</div>
                          <div className="text-sm text-gray-500">{agent.description.substring(0, 50)}...</div>
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
                            {userInfo.username}
                          </div>
                          <div className="text-xs text-gray-500">
                            {userInfo.email}
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