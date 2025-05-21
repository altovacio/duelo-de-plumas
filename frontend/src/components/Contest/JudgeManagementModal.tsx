import React, { useState, useEffect } from 'react';
import { getContestJudges, assignJudgeToContest, removeJudgeFromContest, ContestJudge } from '../../services/contestService';
import { getAgents, Agent } from '../../services/agentService';
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
      
      // Also load AI agents for the second tab
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
      const availableAgents = judgeAgents.filter(agent => 
        !judges.some(judge => judge.agent_judge_id === agent.id)
      );
      
      setAvailableAIAgents(availableAgents);
    } catch (err) {
      console.error('Error fetching AI agents:', err);
      // Don't set error state to avoid disrupting the main judges view
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
                <div className="flex justify-between items-center mb-4">
                  <h4 className="text-lg font-medium text-gray-700">Add Human Judge</h4>
                  <button
                    onClick={handleAddHumanJudge}
                    disabled={isAddingJudgeId !== null || !user}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
                  >
                    Add Yourself as Judge
                  </button>
                </div>
                <p className="text-sm text-gray-500 mb-2">
                  Add yourself as a human judge to this contest. As the contest creator, you can also add yourself to manually judge submissions.
                  {judgeRestrictions && " This contest has judge restrictions, so only users you specifically assign can be judges."}
                </p>
                <div className="bg-yellow-50 border border-yellow-100 rounded-md p-3 mt-2">
                  <p className="text-sm text-yellow-700">
                    <span className="font-medium">Note:</span> Other users can't be added directly. 
                    {!judgeRestrictions 
                      ? " However, since this contest allows volunteer judges, users can add themselves as judges from the contest page."
                      : " With judge restrictions enabled, you must share the contest link with them and they need to request judge access."}
                  </p>
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
                          <span className="font-medium">{agent.name}</span>
                          <span className="text-xs ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full">
                            {agent.model}
                          </span>
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
                              AI - {judge.ai_model || "Unknown model"}
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