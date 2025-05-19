import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import TextFormModal from '../../components/TextEditor/TextFormModal';
import ContestFormModal from '../../components/Contest/ContestFormModal';
import AgentFormModal from '../../components/Agent/AgentFormModal';
import { getUserTexts, createText, updateText, deleteText, Text as TextType } from '../../services/textService';
import { getUserContests, createContest, updateContest, deleteContest, Contest as ContestType } from '../../services/contestService';
import { getAgents, createAgent, updateAgent, deleteAgent, cloneAgent, Agent as AgentType } from '../../services/agentService';
import { getDashboardData } from '../../services/dashboardService';

type TabType = 'overview' | 'contests' | 'texts' | 'agents' | 'participation' | 'credits';

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  
  // Common state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Text state
  const [isTextModalOpen, setIsTextModalOpen] = useState(false);
  const [selectedText, setSelectedText] = useState<TextType | null>(null);
  const [textsData, setTextsData] = useState<TextType[]>([]);
  
  // Contest state
  const [isContestModalOpen, setIsContestModalOpen] = useState(false);
  const [selectedContest, setSelectedContest] = useState<ContestType | null>(null);
  const [contestsData, setContestsData] = useState<ContestType[]>([]);
  
  // Agent state
  const [isAgentModalOpen, setIsAgentModalOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<AgentType | null>(null);
  const [ownedAgentsData, setOwnedAgentsData] = useState<AgentType[]>([]);
  const [publicAgentsData, setPublicAgentsData] = useState<AgentType[]>([]);
  const [isLoadingPublic, setIsLoadingPublic] = useState(false);
  
  // Editing flags
  const [isEditing, setIsEditing] = useState(false);

  // Fetch data based on active tab
  useEffect(() => {
    if (activeTab === 'texts') {
      fetchTexts();
    } else if (activeTab === 'contests') {
      fetchContests();
    } else if (activeTab === 'agents') {
      fetchAgents();
    } else if (activeTab === 'overview') {
      // For overview, fetch summary data
      fetchOverviewData();
    }
  }, [activeTab]);

  // Text management functions
  const fetchTexts = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const texts = await getUserTexts();
      setTextsData(texts);
    } catch (err) {
      console.error('Error fetching texts:', err);
      setError('Failed to load texts. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenCreateTextModal = () => {
    setIsEditing(false);
    setSelectedText(null);
    setIsTextModalOpen(true);
  };

  const handleOpenEditTextModal = (text: TextType) => {
    setIsEditing(true);
    setSelectedText(text);
    setIsTextModalOpen(true);
  };

  const handleTextSubmit = async (textData: { title: string; content: string; author: string }) => {
    try {
      setIsLoading(true);
      if (isEditing && selectedText) {
        // Update existing text
        const updatedText = await updateText(selectedText.id, textData);
        setTextsData(textsData.map(text => 
          text.id === updatedText.id ? updatedText : text
        ));
      } else {
        // Create new text
        const newText = await createText(textData);
        setTextsData([...textsData, newText]);
      }
      setIsLoading(false);
    } catch (err) {
      console.error('Error with text operation:', err);
      setError(`Failed to ${isEditing ? 'update' : 'create'} text. Please try again later.`);
      setIsLoading(false);
    }
  };

  const handleDeleteText = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this text?')) {
      try {
        setIsLoading(true);
        await deleteText(id);
        setTextsData(textsData.filter(text => text.id !== id));
        setIsLoading(false);
      } catch (err) {
        console.error('Error deleting text:', err);
        setError('Failed to delete text. Please try again later.');
        setIsLoading(false);
      }
    }
  };

  // Contest management functions
  const fetchContests = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const contests = await getUserContests();
      setContestsData(contests);
    } catch (err) {
      console.error('Error fetching contests:', err);
      setError('Failed to load contests. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenCreateContestModal = () => {
    setIsEditing(false);
    setSelectedContest(null);
    setIsContestModalOpen(true);
  };

  const handleOpenEditContestModal = (contest: ContestType) => {
    setIsEditing(true);
    setSelectedContest(contest);
    setIsContestModalOpen(true);
  };

  const handleContestSubmit = async (contestData: { 
    title: string; 
    description: string; 
    is_private: boolean;
    password?: string;
  }) => {
    try {
      setIsLoading(true);
      if (isEditing && selectedContest) {
        // Update existing contest
        const updatedContest = await updateContest(selectedContest.id, contestData);
        setContestsData(contestsData.map(contest => 
          contest.id === updatedContest.id ? updatedContest : contest
        ));
      } else {
        // Create new contest
        const newContest = await createContest(contestData);
        setContestsData([...contestsData, newContest]);
      }
      setIsLoading(false);
    } catch (err) {
      console.error('Error with contest operation:', err);
      setError(`Failed to ${isEditing ? 'update' : 'create'} contest. Please try again later.`);
      setIsLoading(false);
    }
  };

  const handleDeleteContest = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this contest?')) {
      try {
        setIsLoading(true);
        await deleteContest(id);
        setContestsData(contestsData.filter(contest => contest.id !== id));
        setIsLoading(false);
      } catch (err) {
        console.error('Error deleting contest:', err);
        setError('Failed to delete contest. Please try again later.');
        setIsLoading(false);
      }
    }
  };

  // Agent management functions
  const fetchAgents = async () => {
    try {
      // Fetch owned agents
      setIsLoading(true);
      setError(null);
      const myAgents = await getAgents(false); // false = only private agents owned by the user
      setOwnedAgentsData(myAgents);
      setIsLoading(false);
      
      // Fetch public agents
      setIsLoadingPublic(true);
      const publicAgents = await getAgents(true); // true = only public agents
      setPublicAgentsData(publicAgents);
      setIsLoadingPublic(false);
    } catch (err) {
      console.error('Error fetching agents:', err);
      setError('Failed to load agents. Please try again later.');
      setIsLoading(false);
      setIsLoadingPublic(false);
    }
  };

  const handleOpenCreateAgentModal = () => {
    setIsEditing(false);
    setSelectedAgent(null);
    setIsAgentModalOpen(true);
  };

  const handleOpenEditAgentModal = (agent: AgentType) => {
    setIsEditing(true);
    setSelectedAgent(agent);
    setIsAgentModalOpen(true);
  };

  const handleAgentSubmit = async (agentData: {
    name: string;
    description: string;
    type: 'writer' | 'judge';
    prompt: string;
    model: string;
    is_public?: boolean;
  }) => {
    try {
      setIsLoading(true);
      if (isEditing && selectedAgent) {
        // Update existing agent
        const updatedAgent = await updateAgent(selectedAgent.id, agentData);
        setOwnedAgentsData(ownedAgentsData.map(agent => 
          agent.id === updatedAgent.id ? updatedAgent : agent
        ));
      } else {
        // Create new agent
        const newAgent = await createAgent(agentData);
        setOwnedAgentsData([...ownedAgentsData, newAgent]);
      }
      setIsLoading(false);
    } catch (err) {
      console.error('Error with agent operation:', err);
      setError(`Failed to ${isEditing ? 'update' : 'create'} agent. Please try again later.`);
      setIsLoading(false);
    }
  };

  const handleDeleteAgent = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this agent?')) {
      try {
        setIsLoading(true);
        await deleteAgent(id);
        setOwnedAgentsData(ownedAgentsData.filter(agent => agent.id !== id));
        setIsLoading(false);
      } catch (err) {
        console.error('Error deleting agent:', err);
        setError('Failed to delete agent. Please try again later.');
        setIsLoading(false);
      }
    }
  };

  const handleCloneAgent = async (id: number) => {
    try {
      setIsLoading(true);
      const clonedAgent = await cloneAgent(id);
      setOwnedAgentsData([...ownedAgentsData, clonedAgent]);
      setIsLoading(false);
    } catch (err) {
      console.error('Error cloning agent:', err);
      setError('Failed to clone agent. Please try again later.');
      setIsLoading(false);
    }
  };

  // Dashboard overview data
  const fetchOverviewData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const dashboardData = await getDashboardData();
      
      // Update contests data if available
      if (dashboardData.author_contests) {
        setContestsData(dashboardData.author_contests);
      }
      
      // Also fetch texts separately since they're not part of the dashboard endpoint
      fetchTexts();
      
      setIsLoading(false);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data. Please try again later.');
      setIsLoading(false);
    }
  };

  const tabClasses = (tab: TabType) => 
    `px-4 py-2 ${activeTab === tab 
      ? 'font-semibold text-indigo-700 border-b-2 border-indigo-700' 
      : 'text-gray-600 hover:text-indigo-700'}`;

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="p-6">
        <h1 className="text-2xl font-semibold text-gray-800 mb-2">
          My Workspace
        </h1>
        <p className="text-gray-600 mb-6">
          Welcome back, {user?.username}! Manage your contests, texts, and AI agents.
        </p>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="flex space-x-6">
            <button 
              className={tabClasses('overview')}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button 
              className={tabClasses('contests')}
              onClick={() => setActiveTab('contests')}
            >
              My Contests
            </button>
            <button 
              className={tabClasses('texts')}
              onClick={() => setActiveTab('texts')}
            >
              My Texts
            </button>
            <button 
              className={tabClasses('agents')}
              onClick={() => setActiveTab('agents')}
            >
              AI Agents
            </button>
            <button 
              className={tabClasses('participation')}
              onClick={() => setActiveTab('participation')}
            >
              Participation
            </button>
            <button 
              className={tabClasses('credits')}
              onClick={() => setActiveTab('credits')}
            >
              Credits
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div>
          {activeTab === 'overview' && (
            <div>
              <h2 className="text-xl font-medium mb-4">Dashboard Overview</h2>
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-yellow-700">
                      You have <span className="font-medium">0 urgent actions</span> pending.
                    </p>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-700">Credit Balance</h3>
                  <p className="text-2xl font-bold text-indigo-600">{user?.credit_balance}</p>
                </div>
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-700">My Contests</h3>
                  <p className="text-2xl font-bold text-indigo-600">{contestsData.length}</p>
                </div>
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-700">My Texts</h3>
                  <p className="text-2xl font-bold text-indigo-600">{textsData.length}</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'contests' && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-medium">My Contests</h2>
                <button 
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
                  onClick={handleOpenCreateContestModal}
                >
                  Create New Contest
                </button>
              </div>
              
              {error && (
                <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-red-700">{error}</p>
                    </div>
                  </div>
                </div>
              )}
              
              {isLoading ? (
                <div className="flex justify-center items-center h-32">
                  <svg className="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
              ) : contestsData.length > 0 ? (
                <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                  <table className="min-w-full divide-y divide-gray-300">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col" className="py-3 pl-4 pr-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Title</th>
                        <th scope="col" className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Status</th>
                        <th scope="col" className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Type</th>
                        <th scope="col" className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Participants</th>
                        <th scope="col" className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Created</th>
                        <th scope="col" className="relative py-3 pl-3 pr-4">
                          <span className="sr-only">Actions</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 bg-white">
                      {contestsData.map((contest) => (
                        <tr key={contest.id}>
                          <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900">
                            {contest.title}
                          </td>
                          <td className="px-3 py-4 text-sm">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              contest.status === 'open' ? 'bg-green-100 text-green-800' :
                              contest.status === 'evaluation' ? 'bg-yellow-100 text-yellow-800' :
                               'bg-blue-100 text-blue-800'
                            }`}>
                              {contest.status.charAt(0).toUpperCase() + contest.status.slice(1)}
                            </span>
                          </td>
                          <td className="px-3 py-4 text-sm">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              contest.is_private ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'
                            }`}>
                              {contest.is_private ? 'Private' : 'Public'}
                            </span>
                          </td>
                          <td className="px-3 py-4 text-sm text-gray-500">
                            {contest.participant_count || 0}
                          </td>
                          <td className="px-3 py-4 text-sm text-gray-500">
                            {new Date(contest.created_at).toLocaleDateString()}
                          </td>
                          <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium">
                            <button 
                              onClick={() => handleOpenEditContestModal(contest)}
                              className="text-indigo-600 hover:text-indigo-900 mr-3"
                            >
                              Edit
                            </button>
                            <button 
                              onClick={() => handleDeleteContest(contest.id)}
                              className="text-red-600 hover:text-red-900"
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-500 italic">No contests yet. Create your first contest!</p>
              )}
            </div>
          )}

          {activeTab === 'texts' && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-medium">My Texts</h2>
                <button 
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
                  onClick={handleOpenCreateTextModal}
                >
                  Create New Text
                </button>
              </div>
              
              {error && (
                <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-red-700">{error}</p>
                    </div>
                  </div>
                </div>
              )}
              
              {isLoading ? (
                <div className="flex justify-center items-center h-32">
                  <svg className="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
              ) : textsData.length > 0 ? (
                <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                  <table className="min-w-full divide-y divide-gray-300">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col" className="py-3 pl-4 pr-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Title</th>
                        <th scope="col" className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Content Preview</th>
                        <th scope="col" className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Author</th>
                        <th scope="col" className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Created</th>
                        <th scope="col" className="relative py-3 pl-3 pr-4">
                          <span className="sr-only">Actions</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 bg-white">
                      {textsData.map((text) => (
                        <tr key={text.id}>
                          <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900">
                            {text.title}
                          </td>
                          <td className="px-3 py-4 text-sm text-gray-500">
                            {text.content.length > 50 
                              ? `${text.content.substring(0, 50)}...` 
                              : text.content}
                          </td>
                          <td className="px-3 py-4 text-sm text-gray-500">
                            {text.author}
                          </td>
                          <td className="px-3 py-4 text-sm text-gray-500">
                            {new Date(text.created_at).toLocaleDateString()}
                          </td>
                          <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium">
                            <button 
                              className="text-indigo-600 hover:text-indigo-900 mr-4"
                              onClick={() => handleOpenEditTextModal(text)}
                            >
                              Edit
                            </button>
                            <button 
                              className="text-red-600 hover:text-red-900"
                              onClick={() => handleDeleteText(text.id)}
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-500 italic">No texts yet. Create your first text!</p>
              )}
            </div>
          )}

          {activeTab === 'agents' && (
            <div>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-medium">My AI Agents</h2>
                <button 
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
                  onClick={handleOpenCreateAgentModal}
                >
                  Create New Agent
                </button>
              </div>
              {error && (
                <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-red-700">{error}</p>
                    </div>
                  </div>
                </div>
              )}
              <div className="mb-8">
                <h3 className="text-lg font-medium text-gray-800 mb-4">My Agents</h3>
                {isLoading ? (
                  <div className="flex justify-center items-center h-32">
                    <svg className="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </div>
                ) : ownedAgentsData.length > 0 ? (
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {ownedAgentsData.map((agent) => (
                      <div key={agent.id} className="bg-white overflow-hidden shadow rounded-lg divide-y divide-gray-200">
                        <div className="px-4 py-5 sm:px-6">
                          <div className="flex justify-between items-start">
                            <h3 className="text-lg font-medium text-gray-900 truncate">{agent.name}</h3>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              agent.type === 'writer' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                            }`}>
                              {agent.type.charAt(0).toUpperCase() + agent.type.slice(1)}
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-gray-500 line-clamp-2">{agent.description}</p>
                        </div>
                        <div className="px-4 py-4 sm:px-6 flex justify-between items-center">
                          <div className="text-sm text-gray-500">
                            Model: {agent.model}
                          </div>
                          <div>
                            <button 
                              onClick={() => handleOpenEditAgentModal(agent)}
                              className="text-indigo-600 hover:text-indigo-900 mr-3 text-sm"
                            >
                              Edit
                            </button>
                            <button 
                              onClick={() => handleDeleteAgent(agent.id)}
                              className="text-red-600 hover:text-red-900 text-sm"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 italic">You haven't created any AI agents yet.</p>
                )}
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-800 mb-4">Public Agents</h3>
                {isLoadingPublic ? (
                  <div className="flex justify-center items-center h-32">
                    <svg className="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </div>
                ) : publicAgentsData.length > 0 ? (
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {publicAgentsData.map((agent) => (
                      <div key={agent.id} className="bg-white overflow-hidden shadow rounded-lg divide-y divide-gray-200">
                        <div className="px-4 py-5 sm:px-6">
                          <div className="flex justify-between items-start">
                            <h3 className="text-lg font-medium text-gray-900 truncate">{agent.name}</h3>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              agent.type === 'writer' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                            }`}>
                              {agent.type.charAt(0).toUpperCase() + agent.type.slice(1)}
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-gray-500 line-clamp-2">{agent.description}</p>
                        </div>
                        <div className="px-4 py-4 sm:px-6 flex justify-between items-center">
                          <div className="text-sm text-gray-500">
                            Model: {agent.model}
                          </div>
                          <button 
                            onClick={() => handleCloneAgent(agent.id)}
                            className="text-indigo-600 hover:text-indigo-900 text-sm"
                          >
                            Clone to My Agents
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 italic">No public agents available yet.</p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'participation' && (
            <div>
              <h2 className="text-xl font-medium mb-4">My Participation</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">Contests where I'm an author</h3>
                  <p className="text-gray-500 italic">Not participating in any contests as an author.</p>
                </div>
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">Contests where I'm a judge</h3>
                  <p className="text-gray-500 italic">Not participating in any contests as a judge.</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'credits' && (
            <div>
              <h2 className="text-xl font-medium mb-4">Credits Management</h2>
              <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
                <h3 className="font-medium text-gray-700">Current Balance</h3>
                <p className="text-2xl font-bold text-indigo-600">{user?.credit_balance} credits</p>
              </div>
              <h3 className="font-medium text-gray-700 mb-2">Transaction History</h3>
              <p className="text-gray-500 italic">No transaction history available.</p>
            </div>
          )}
        </div>
      </div>

      {/* Text Form Modal */}
      <TextFormModal
        isOpen={isTextModalOpen}
        onClose={() => setIsTextModalOpen(false)}
        onSubmit={handleTextSubmit}
        initialText={selectedText ? { 
          title: selectedText.title, 
          content: selectedText.content,
          author: selectedText.author 
        } : undefined}
        isEditing={isEditing}
      />

      {/* Contest Form Modal */}
      <ContestFormModal
        isOpen={isContestModalOpen}
        onClose={() => setIsContestModalOpen(false)}
        onSubmit={handleContestSubmit}
        initialContest={selectedContest ? {
          title: selectedContest.title,
          description: selectedContest.description,
          is_private: selectedContest.is_private,
          password: selectedContest.password || undefined
        } : undefined}
        isEditing={isEditing}
      />

      {/* Agent Form Modal */}
      <AgentFormModal
        isOpen={isAgentModalOpen}
        onClose={() => setIsAgentModalOpen(false)}
        onSubmit={handleAgentSubmit}
        initialAgent={selectedAgent ? {
          name: selectedAgent.name,
          description: selectedAgent.description,
          type: selectedAgent.type,
          prompt: selectedAgent.prompt,
          model: selectedAgent.model,
          is_public: selectedAgent.is_public
        } : undefined}
        isEditing={isEditing}
        isAdmin={user?.is_admin}
      />
    </div>
  );
};

export default DashboardPage; 