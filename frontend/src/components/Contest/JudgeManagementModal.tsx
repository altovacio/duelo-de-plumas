import React, { useState, useEffect } from 'react';
import { getContestJudges, assignJudgeToContest, removeJudgeFromContest, ContestJudge } from '../../services/contestService';
import { getAgents, Agent } from '../../services/agentService';
import { searchUsers, User } from '../../services/userService';
import { toast } from 'react-hot-toast';
import { useAuth } from '../../hooks/useAuth';
import { Link } from 'react-router-dom';

interface JudgeManagementModalProps {
  isOpen: boolean;
  onClose: () => void;
  contestId: number;
  contestTitle: string;
  judgeRestrictions: boolean;
}

type JudgeType = 'human' | 'ai';

const JudgeManagementModal: React.FC<JudgeManagementModalProps> = ({
  isOpen,
  onClose,
  contestId,
  contestTitle,
  judgeRestrictions
}) => {
  const { user } = useAuth();
  const [judges, setJudges] = useState<ContestJudge[]>([]);
  const [activeTab, setActiveTab] = useState<JudgeType>('human');
  const [availableAIAgents, setAvailableAIAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingAgents, setIsLoadingAgents] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRemovingJudgeId, setIsRemovingJudgeId] = useState<number | null>(null);
  const [isAddingJudgeId, setIsAddingJudgeId] = useState<number | null>(null);
  
  // User search state
  const [userSearchQuery, setUserSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchJudges();
    }
  }, [isOpen, contestId]);

  const fetchJudges = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const judgesData = await getContestJudges(contestId);
      setJudges(judgesData);
      
      // Refresh available AI agents after judges are updated to ensure proper filtering
      fetchAvailableAIAgents();
    } catch (err: any) {
      console.error('Error fetching judges:', err);
      // Handle network errors more specifically
      if (err.code === 'ERR_NETWORK') {
        setError('Network error: Could not connect to the server. This might be a CORS issue or the server is down.');
      } else {
        setError(`Failed to load judges: ${err.message || 'Please try again later.'}`);
      }
      
      // Set an empty array for judges to avoid null/undefined errors
      setJudges([]);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAvailableAIAgents = async () => {
    try {
      setIsLoadingAgents(true);
      // Get judges that can be used
      const agents = await getAgents();
      
      // Filter to only include judge-type agents
      const judgeAgents = agents.filter(agent => agent.type === 'judge');
      
      // Filter out agents that are already assigned as judges
      // Use the current judges state to filter properly
      const availableAgents = judgeAgents.filter(agent => 
        !judges.some(judge => judge.agent_judge_id === agent.id)
      );
      
      setAvailableAIAgents(availableAgents);
    } catch (err) {
      console.error('Error fetching AI agents:', err);
      // Don't set error state to avoid disrupting the main judges view
      setAvailableAIAgents([]);
    } finally {
      setIsLoadingAgents(false);
    }
  };

  const handleAddHumanJudge = async () => {
    // Since we don't have a user search API, we can just add the current user as a judge
    if (!user) return;
    
    try {
      setIsAddingJudgeId(user.id);
      await assignJudgeToContest(contestId, { user_id: user.id });
      // Refresh judges list
      await fetchJudges();
      toast.success('You have been added as a judge');
    } catch (err: any) {
      console.error('Error adding human judge:', err);
      
      // Handle network errors and common status codes
      if (err.code === 'ERR_NETWORK') {
        toast.error('Network error: Could not connect to the server');
      } else if (err.response) {
        // Handle specific HTTP status codes
        if (err.response.status === 409) {
          toast.success('You are already a judge for this contest');
        } else {
          toast.error(`Error: ${err.response.data?.detail || err.message || 'Failed to add judge'}`);
        }
      } else {
        toast.error('Failed to add judge. Please try again.');
      }
    } finally {
      setIsAddingJudgeId(null);
    }
  };

  // User search functionality
  const handleUserSearch = async (query: string) => {
    setUserSearchQuery(query);
    
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }
    
    try {
      setIsSearching(true);
      const results = await searchUsers(query);
      // Filter out users who are already judges
      const availableUsers = results.filter(searchUser => 
        !judges.some(judge => judge.user_judge_id === searchUser.id)
      );
      setSearchResults(availableUsers);
    } catch (err) {
      console.error('Error searching users:', err);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleAddUserAsJudge = async (userId: number) => {
    try {
      setIsAddingJudgeId(userId);
      await assignJudgeToContest(contestId, { user_id: userId });
      // Refresh judges list
      await fetchJudges();
      // Clear search
      setUserSearchQuery('');
      setSearchResults([]);
      toast.success('User added as judge successfully');
    } catch (err: any) {
      console.error('Error adding user as judge:', err);
      
      // Handle network errors and common status codes
      if (err.code === 'ERR_NETWORK') {
        toast.error('Network error: Could not connect to the server');
      } else if (err.response) {
        // Handle specific HTTP status codes
        if (err.response.status === 409) {
          toast.success('This user is already a judge for this contest');
        } else {
          toast.error(`Error: ${err.response.data?.detail || err.message || 'Failed to add judge'}`);
        }
      } else {
        toast.error('Failed to add judge. Please try again.');
      }
    } finally {
      setIsAddingJudgeId(null);
    }
  };

  const handleAddAIJudge = async (agentId: number) => {
    try {
      setIsAddingJudgeId(agentId);
      await assignJudgeToContest(contestId, { agent_id: agentId });
      // Refresh judges list
      await fetchJudges();
      toast.success('AI judge added successfully');
    } catch (err: any) {
      console.error('Error adding AI judge:', err);
      
      // Handle network errors and common status codes
      if (err.code === 'ERR_NETWORK') {
        toast.error('Network error: Could not connect to the server');
      } else if (err.response) {
        // Handle specific HTTP status codes
        if (err.response.status === 409) {
          toast.success('This AI judge is already assigned to this contest');
        } else {
          toast.error(`Error: ${err.response.data?.detail || err.message || 'Failed to add AI judge'}`);
        }
      } else {
        toast.error('Failed to add AI judge. Please try again.');
      }
    } finally {
      setIsAddingJudgeId(null);
    }
  };

  const handleRemoveJudge = async (judgeAssignmentId: number) => {
    try {
      setIsRemovingJudgeId(judgeAssignmentId);
      await removeJudgeFromContest(contestId, judgeAssignmentId);
      // Refresh judges list
      await fetchJudges();
      toast.success('Judge removed successfully');
    } catch (err: any) {
      console.error('Error removing judge:', err);
      
      // Handle network errors and common status codes
      if (err.code === 'ERR_NETWORK') {
        toast.error('Network error: Could not connect to the server');
      } else if (err.response) {
        toast.error(`Error: ${err.response.data?.detail || err.message || 'Failed to remove judge'}`);
      } else {
        toast.error('Failed to remove judge. Please try again.');
      }
    } finally {
      setIsRemovingJudgeId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800">
            Manage Judges for: {contestTitle}
          </h3>
        </div>
        
        <div className="px-6 py-4 overflow-y-auto flex-grow">
          {error && (
            <div className="mb-4 p-3 bg-red-100 text-red-700 border border-red-200 rounded-md">
              {error}
            </div>
          )}
          
          {/* Tabs for Human vs AI judges */}
          <div className="border-b border-gray-200 mb-4">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('human')}
                className={`py-2 px-1 ${
                  activeTab === 'human'
                    ? 'border-b-2 border-indigo-500 font-medium text-indigo-600'
                    : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Human Judges
              </button>
              <button
                onClick={() => setActiveTab('ai')}
                className={`py-2 px-1 ${
                  activeTab === 'ai'
                    ? 'border-b-2 border-indigo-500 font-medium text-indigo-600'
                    : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                AI Judges
              </button>
            </nav>
          </div>
          
          {/* Human Judges Tab */}
          {activeTab === 'human' && (
            <div>
              <div className="mb-6">
                <h4 className="text-lg font-medium text-gray-700 mb-4">Add Human Judge</h4>
                <p className="text-sm text-gray-500 mb-4">
                  Search for users by username or email to add them as judges for this contest.
                </p>
                
                <div className="space-y-4">
                  {/* User Search Input */}
                  <div>
                    <label htmlFor="userSearch" className="block text-sm font-medium text-gray-700 mb-1">
                      Search Users
                    </label>
                    <input
                      id="userSearch"
                      type="text"
                      placeholder="Type username or email..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      value={userSearchQuery}
                      onChange={(e) => handleUserSearch(e.target.value)}
                    />
                  </div>
                  
                  {/* Search Results */}
                  {userSearchQuery.length >= 2 && (
                    <div className="border rounded-md">
                      {isSearching ? (
                        <div className="p-4 text-center text-gray-500">
                          <div className="inline-flex items-center">
                            <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Searching...
                          </div>
                        </div>
                      ) : searchResults.length === 0 ? (
                        <div className="p-4 text-center text-gray-500">
                          No users found matching "{userSearchQuery}"
                        </div>
                      ) : (
                        <ul className="divide-y">
                          {searchResults.map(searchUser => (
                            <li key={searchUser.id} className="flex justify-between items-center p-3 hover:bg-gray-50">
                              <span className="font-medium">{searchUser.username}</span>
                              <button
                                onClick={() => handleAddUserAsJudge(searchUser.id)}
                                disabled={isAddingJudgeId === searchUser.id}
                                className="text-sm px-3 py-1 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50"
                              >
                                {isAddingJudgeId === searchUser.id ? 'Adding...' : 'Add as Judge'}
                              </button>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                  
                  {/* Quick Add Self Option */}
                  <div className="border-t pt-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Add yourself as a judge:</span>
                      <button
                        onClick={handleAddHumanJudge}
                        disabled={isAddingJudgeId !== null || !user}
                        className="px-3 py-1 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 text-sm"
                      >
                        Add Yourself
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* AI Judges Tab */}
          {activeTab === 'ai' && (
            <div>
              <div className="mb-6">
                <h4 className="text-lg font-medium text-gray-700 mb-2">Add AI Judge</h4>
                <p className="text-sm text-gray-500 mb-4">
                  Add your AI judges to this contest. AI judges will evaluate submissions based on your prompts.
                  You can have multiple AI judges with different evaluation criteria for a more comprehensive assessment.
                </p>
                
                {isLoadingAgents ? (
                  <div className="flex justify-center items-center h-24">
                    <svg className="animate-spin h-6 w-6 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </div>
                ) : availableAIAgents.length === 0 ? (
                  <div>
                    <p className="text-gray-500 italic">
                      You don't have any AI judges available to add.
                      {judges.some(j => j.agent_judge_id) ? 
                        " You might have already added all your AI judges to this contest." :
                        " Please create a judge AI agent in your dashboard first."
                      }
                    </p>
                    <Link 
                      to="/dashboard" 
                      className="mt-2 inline-block px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                      onClick={() => onClose()}
                    >
                      Create AI Judge in Dashboard
                    </Link>
                  </div>
                ) : (
                  <ul className="border rounded-md divide-y">
                    {availableAIAgents.map(agent => (
                      <li key={agent.id} className="flex justify-between items-center p-3 hover:bg-gray-50">
                        <div>
                          <div className="flex items-center">
                            <span className="font-medium">{agent.name}</span>
                            <span className="text-xs ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full">
                              {agent.model}
                            </span>
                            {/* Remove voting status tags from available agents - they aren't judges yet */}
                          </div>
                          <p className="text-sm text-gray-500 mt-1">{agent.description}</p>
                        </div>
                        <button
                          onClick={() => handleAddAIJudge(agent.id)}
                          disabled={isAddingJudgeId === agent.id}
                          className="text-sm px-3 py-1 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50"
                        >
                          {isAddingJudgeId === agent.id ? 'Adding...' : 'Add as Judge'}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
          
          {/* Current Judges List - shown in both tabs */}
          <div>
            <h4 className="text-lg font-medium text-gray-700 mb-2">Current Judges</h4>
            {isLoading ? (
              <div className="flex justify-center items-center h-32">
                <svg className="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            ) : judges.length === 0 ? (
              <p className="text-gray-500 italic">No judges assigned to this contest yet.</p>
            ) : (
              <ul className="border rounded-md divide-y">
                {judges
                  .filter(judge => activeTab === 'human' ? !judge.agent_judge_id : !!judge.agent_judge_id)
                  .map(judge => (
                  <li key={judge.id} className="flex justify-between items-center p-3 hover:bg-gray-50">
                    <div className="flex items-center">
                      <div>
                        <div className="flex items-center">
                          <span className="font-medium">{judge.user_name || judge.agent_name || 'Unknown'}</span>
                          {judge.agent_judge_id && (
                            <span className="ml-2 text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full">
                              AI
                            </span>
                          )}
                          {judge.has_voted && (
                            <span className="ml-2 text-xs px-2 py-0.5 bg-green-100 text-green-800 rounded-full">
                              ✓ Voted
                            </span>
                          )}
                          {!judge.has_voted && judge.agent_judge_id && (
                            <span className="ml-2 text-xs px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded-full">
                              Pending
                            </span>
                          )}
                        </div>
                        {judge.user_email && <span className="text-gray-500 text-sm block mt-1">{judge.user_email}</span>}
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemoveJudge(judge.id)}
                      disabled={isRemovingJudgeId === judge.id}
                      className="text-sm px-3 py-1 bg-red-500 text-white rounded-md hover:bg-red-600 disabled:opacity-50"
                    >
                      {isRemovingJudgeId === judge.id ? 'Removing...' : 'Remove'}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
        
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default JudgeManagementModal; 