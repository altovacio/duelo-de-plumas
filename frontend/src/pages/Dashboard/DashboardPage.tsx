import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import TextFormModal from '../../components/TextEditor/TextFormModal';
import ContestFormModal from '../../components/Contest/ContestFormModal';
import AgentFormModal from '../../components/Agent/AgentFormModal';
import { getUserTexts, createText, updateText, deleteText, Text as TextType } from '../../services/textService';
import { getUserContests, createContest, updateContest, deleteContest, Contest as ContestType, getContestSubmissions, ContestText as ContestSubmissionType, removeSubmissionFromContest, getAuthorParticipation, getJudgeParticipation } from '../../services/contestService';
import { getAgents, createAgent, updateAgent, deleteAgent, cloneAgent, Agent as AgentType } from '../../services/agentService';
import { getDashboardData } from '../../services/dashboardService';
import { toast } from 'react-hot-toast';
import { Link } from 'react-router-dom';
import apiClient from '../../utils/apiClient';
import JudgeManagementModal from '../../components/Contest/JudgeManagementModal';
import { useAuthStore } from '../../store/authStore';
import FullTextModal from '../../components/Common/FullTextModal';

type TabType = 'overview' | 'contests' | 'texts' | 'agents' | 'participation' | 'credits';

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const setUser = useAuthStore(state => state.setUser);
  const loadUser = useAuthStore(state => state.loadUser);
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
  
  // State for submissions modal
  const [isSubmissionsModalOpen, setIsSubmissionsModalOpen] = useState(false);
  const [selectedContestForSubmissions, setSelectedContestForSubmissions] = useState<ContestType | null>(null);
  const [submissionsForSelectedContest, setSubmissionsForSelectedContest] = useState<ContestSubmissionType[]>([]);
  const [isLoadingSubmissions, setIsLoadingSubmissions] = useState(false);
  const [errorSubmissions, setErrorSubmissions] = useState<string | null>(null);
  
  // State for viewing full submission content
  const [isFullContentModalOpen, setIsFullContentModalOpen] = useState(false);
  const [selectedSubmissionForContent, setSelectedSubmissionForContent] = useState<ContestSubmissionType | null>(null);

  // State for removing a submission
  const [isRemovingSubmissionId, setIsRemovingSubmissionId] = useState<number | null>(null);
  
  // Agent state
  const [isAgentModalOpen, setIsAgentModalOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<AgentType | null>(null);
  const [ownedAgentsData, setOwnedAgentsData] = useState<AgentType[]>([]);
  const [publicAgentsData, setPublicAgentsData] = useState<AgentType[]>([]);
  const [isLoadingPublic, setIsLoadingPublic] = useState(false);
  
  // Editing flags
  const [isEditing, setIsEditing] = useState(false);

  // Add at the top with other state definitions:
  const [participationContests, setParticipationContests] = useState<{
    asAuthor: ContestType[];
    asJudge: ContestType[];
  }>({ asAuthor: [], asJudge: [] });
  const [isLoadingParticipation, setIsLoadingParticipation] = useState(false);

  // Add the following state variables in the component after other state definitions
  const [isJudgeModalOpen, setIsJudgeModalOpen] = useState(false);
  const [selectedContestForJudges, setSelectedContestForJudges] = useState<ContestType | null>(null);

  // Add the following state variables for text search
  const [textSearchQuery, setTextSearchQuery] = useState('');
  const [filteredTexts, setFilteredTexts] = useState<TextType[]>([]);
  const [isCreateTextDropdownOpen, setIsCreateTextDropdownOpen] = useState(false);

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
    } else if (activeTab === 'participation') {
      fetchParticipation();
    } else if (activeTab === 'credits') {
      // Credits tab - user data is already up-to-date via auth system
      // No need to refresh user data here
    }
  }, [activeTab]);

  // Helper function to refresh user data
  const refreshUserData = async () => {
    // Note: User data is automatically kept up-to-date by the auth system
    // Only refresh if absolutely necessary (e.g., after credit transactions)
    try {
      await loadUser();
    } catch (err) {
      console.error('Error refreshing user data:', err);
    }
  };

  // Text management functions
  const fetchTexts = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const texts = await getUserTexts();
      setTextsData(texts);
      setFilteredTexts(texts);
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

  const handleContestSubmit = async (contestDataFromForm: { 
    title: string; 
    description: string; 
    is_private: boolean;
    password?: string;
    end_date?: string; 
    judge_restrictions?: boolean;
    author_restrictions?: boolean;
    min_votes_required?: number;
    status?: 'open' | 'evaluation' | 'closed';
  }) => {
    try {
      setIsLoading(true);
      if (isEditing && selectedContest) {
        const { end_date, judge_restrictions, author_restrictions, ...restOfForm } = contestDataFromForm;
        const dataToUpdate: Partial<Omit<ContestType, 'id' | 'creator' | 'created_at' | 'updated_at' | 'participant_count' | 'text_count' | 'has_password'>> = {
          ...restOfForm,
          end_date: end_date === undefined || end_date === '' ? null : end_date,
          judge_restrictions: judge_restrictions === undefined ? false : judge_restrictions,
          author_restrictions: author_restrictions === undefined ? false : author_restrictions,
        };

        if (dataToUpdate.status === undefined && selectedContest.status) {
            dataToUpdate.status = selectedContest.status;
        }

        const updatedContest = await updateContest(selectedContest.id, dataToUpdate as Omit<ContestType, 'id' | 'creator' | 'created_at' | 'updated_at' | 'participant_count' | 'text_count' | 'has_password'>);
        setContestsData(contestsData.map(contest => 
          contest.id === updatedContest.id ? updatedContest : contest
        ));
      } else {
        const { end_date, judge_restrictions, author_restrictions, ...restOfCreationForm } = contestDataFromForm;
        const creationData: Partial<Omit<ContestType, 'id' | 'creator' | 'created_at' | 'updated_at' | 'participant_count' | 'text_count' | 'has_password' | 'status'>> & { status?: 'open' | 'evaluation' | 'closed' } = {
            ...restOfCreationForm,
            end_date: end_date === undefined || end_date === '' ? null : end_date,
            judge_restrictions: judge_restrictions === undefined ? false : judge_restrictions,
            author_restrictions: author_restrictions === undefined ? false : author_restrictions,
        };
        if (contestDataFromForm.status) {
            creationData.status = contestDataFromForm.status;
        }

        const newContest = await createContest(creationData as any);
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
    is_public?: boolean;
  }) => {
    try {
      // Remember current form submission state for UI message
      const isCreatingNew = !isEditing;
      
      // Create agent data object that includes all required fields
      // This addresses the model type issue by handling it separately
      const apiAgentData = {
        name: agentData.name,
        description: agentData.description,
        type: agentData.type,
        prompt: agentData.prompt,
        is_public: agentData.is_public
      };
      
      if (isEditing && selectedAgent) {
        // Update existing agent
        await updateAgent(selectedAgent.id, apiAgentData);
        toast.success(`Agent "${agentData.name}" updated successfully!`);
      } else {
        // Create new agent
        await createAgent(apiAgentData);
        toast.success(`Agent "${agentData.name}" created successfully!`);
      }
      
      // Reset UI state
      setIsEditing(false);
      setSelectedAgent(null);
      setIsAgentModalOpen(false);
      
      // Refresh agent data
      fetchAgents();
    } catch (err) {
      console.error('Error submitting agent:', err);
      setError('Failed to save agent. Please try again.');
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

  const handleOpenSubmissionsModal = async (contest: ContestType) => {
    setSelectedContestForSubmissions(contest);
    setIsSubmissionsModalOpen(true);
    setIsLoadingSubmissions(true);
    setErrorSubmissions(null);
    try {
      const submissions = await getContestSubmissions(contest.id);
      setSubmissionsForSelectedContest(submissions);
    } catch (err) {
      console.error('Error fetching submissions:', err);
      setErrorSubmissions('Failed to load submissions. Please try again later.');
      setSubmissionsForSelectedContest([]); // Clear previous submissions on error
    } finally {
      setIsLoadingSubmissions(false);
    }
  };

  const handleCloseSubmissionsModal = () => {
    setIsSubmissionsModalOpen(false);
    setSelectedContestForSubmissions(null);
    setSubmissionsForSelectedContest([]);
    setIsLoadingSubmissions(false);
    setErrorSubmissions(null);
  };

  const handleOpenFullContentModal = (submission: ContestSubmissionType) => {
    setSelectedSubmissionForContent(submission);
    setIsFullContentModalOpen(true);
  };

  const handleCloseFullContentModal = () => {
    setIsFullContentModalOpen(false);
    setSelectedSubmissionForContent(null);
  };

  const handleRemoveSubmission = async (submissionId: number) => {
    if (!selectedContestForSubmissions) return;

    const submissionToRemove = submissionsForSelectedContest.find(s => s.id === submissionId);
    if (!submissionToRemove) return;

    if (!window.confirm(`Are you sure you want to remove the submission "${submissionToRemove.title || 'Untitled Submission'}"? This action cannot be undone.`)) {
      return;
    }

    setIsRemovingSubmissionId(submissionId);
    try {
      await removeSubmissionFromContest(selectedContestForSubmissions.id, submissionId);
      // Refresh the list
      const updatedSubmissions = await getContestSubmissions(selectedContestForSubmissions.id);
      setSubmissionsForSelectedContest(updatedSubmissions);
      toast.success(`Submission "${submissionToRemove.title || 'Untitled Submission'}" removed successfully.`);
    } catch (err) {
      console.error('Error removing submission:', err);
      toast.error('Failed to remove submission. Please try again.');
    } finally {
      setIsRemovingSubmissionId(null);
    }
  };

  const tabClasses = (tab: TabType) => 
    `px-4 py-2 ${activeTab === tab 
      ? 'font-semibold text-indigo-700 border-b-2 border-indigo-700' 
      : 'text-gray-600 hover:text-indigo-700'}`;

  // Add this function to fetch participation data
  const fetchParticipation = async () => {
    try {
      setIsLoadingParticipation(true);
      setError(null);
      
      // Use the correct API endpoints from contestService
      const [authorData, judgeData] = await Promise.all([
        getAuthorParticipation(),
        getJudgeParticipation()
      ]);
      
      setParticipationContests({
        asAuthor: authorData,
        asJudge: judgeData
      });
      
      setIsLoadingParticipation(false);
    } catch (err) {
      console.error('Error fetching participation data:', err);
      setError('Failed to load participation data');
      setIsLoadingParticipation(false);
    }
  };

  // Add function to handle opening the judge management modal
  const handleOpenJudgeManagementModal = (contest: ContestType) => {
    setSelectedContestForJudges(contest);
    setIsJudgeModalOpen(true);
  };

  // Add this function to handle status change
  const handleStatusChange = async (contestId: number, newStatus: 'open' | 'evaluation' | 'closed') => {
    try {
      await updateContest(contestId, { status: newStatus });
      // Refresh contests list
      fetchContests();
      toast.success('Contest status updated successfully');
    } catch (error) {
      console.error('Error updating contest status:', error);
      toast.error('Failed to update contest status');
    }
  };

  // Add this useEffect to update filtered texts when search query changes
  useEffect(() => {
    if (textsData.length > 0) {
      const filtered = textsData.filter(text => 
        text.title.toLowerCase().includes(textSearchQuery.toLowerCase()) ||
        text.content.toLowerCase().includes(textSearchQuery.toLowerCase()) ||
        text.author.toLowerCase().includes(textSearchQuery.toLowerCase())
      );
      setFilteredTexts(filtered);
    }
  }, [textSearchQuery, textsData]);

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
                  <p className="text-2xl font-bold text-indigo-600">
                    {user?.credits !== undefined ? `${user.credits} credits` : 'Loading...'}
                  </p>
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
                            <Link 
                              to={`/contests/${contest.id}`}
                              className="text-indigo-600 hover:text-indigo-900 hover:underline"
                            >
                              {contest.title}
                            </Link>
                          </td>
                          <td className="px-3 py-4 text-sm">
                            <select
                              value={contest.status}
                              onChange={(e) => handleStatusChange(contest.id, e.target.value as 'open' | 'evaluation' | 'closed')}
                              className={`px-2.5 py-1 rounded text-xs font-medium border-0 ${
                                contest.status === 'open' ? 'bg-green-100 text-green-800' :
                                contest.status === 'evaluation' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-blue-100 text-blue-800'
                              }`}
                            >
                              <option value="open">Open</option>
                              <option value="evaluation">Evaluation</option>
                              <option value="closed">Closed</option>
                            </select>
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
                              onClick={() => handleOpenSubmissionsModal(contest)}
                              className="text-green-600 hover:text-green-900 mr-3"
                            >
                              View Submissions
                            </button>
                            <button 
                              onClick={() => handleOpenJudgeManagementModal(contest)}
                              className="text-blue-600 hover:text-blue-900 mr-3"
                            >
                              Manage Judges
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
                <div className="flex space-x-2">
                  <div className="relative">
                    <button
                      className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 flex items-center"
                      onClick={() => setIsCreateTextDropdownOpen(!isCreateTextDropdownOpen)}
                    >
                      <span>Create New Text</span>
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-1" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </button>
                    {isCreateTextDropdownOpen && (
                      <div className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg z-10">
                        <div className="py-1">
                          <Link 
                            to="/editor"
                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                            onClick={() => setIsCreateTextDropdownOpen(false)}
                          >
                            Full Page Editor
                          </Link>
                          <button
                            onClick={() => {
                              setIsCreateTextDropdownOpen(false);
                              // Handle PDF upload option
                              toast("PDF upload feature coming soon!");
                            }}
                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            Upload PDF
                          </button>
                          <Link
                            to="/ai-writer"
                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                            onClick={() => setIsCreateTextDropdownOpen(false)}
                          >
                            Use AI Writer
                          </Link>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="mb-6">
                <input
                  type="text"
                  placeholder="Search texts by title, content, or author..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={textSearchQuery}
                  onChange={(e) => {
                    setTextSearchQuery(e.target.value);
                  }}
                />
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
              ) : filteredTexts.length > 0 ? (
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
                      {filteredTexts.map((text) => (
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
                <p className="text-gray-500 italic">No texts found matching your search. Create a new text to get started!</p>
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
              
              {isLoadingParticipation ? (
                <div className="flex justify-center items-center h-32">
                  <svg className="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-medium text-gray-700 mb-2">Contests where I'm an author</h3>
                    {participationContests.asAuthor.length > 0 ? (
                      <div className="bg-white shadow rounded-md overflow-hidden">
                        <ul className="divide-y divide-gray-200">
                          {participationContests.asAuthor.map(contest => (
                            <li key={contest.id} className="px-4 py-3 hover:bg-gray-50">
                              <div className="flex justify-between">
                                <div>
                                  <Link to={`/contests/${contest.id}`} className="text-indigo-600 hover:text-indigo-900 font-medium">
                                    {contest.title}
                                  </Link>
                                  <div className="flex mt-1 space-x-2">
                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                      contest.status === 'open' ? 'bg-green-100 text-green-800' :
                                      contest.status === 'evaluation' ? 'bg-yellow-100 text-yellow-800' :
                                       'bg-blue-100 text-blue-800'
                                    }`}>
                                      {contest.status && typeof contest.status === 'string' 
                                        ? contest.status.charAt(0).toUpperCase() + contest.status.slice(1) 
                                        : 'Unknown'}
                                    </span>
                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                      contest.is_private ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'
                                    }`}>
                                      {contest.is_private ? 'Private' : 'Public'}
                                    </span>
                                  </div>
                                </div>
                                <div className="text-sm text-gray-500">
                                  {contest.created_at ? new Date(contest.created_at).toLocaleDateString() : ''}
                                </div>
                              </div>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : (
                      <p className="text-gray-500 italic">Not participating in any contests as an author.</p>
                    )}
                  </div>
                  
                  <div>
                    <h3 className="font-medium text-gray-700 mb-2">Contests where I'm a judge</h3>
                    {participationContests.asJudge.length > 0 ? (
                      <div className="bg-white shadow rounded-md overflow-hidden">
                        <ul className="divide-y divide-gray-200">
                          {participationContests.asJudge.map(contest => (
                            <li key={contest.id} className="px-4 py-3 hover:bg-gray-50">
                              <div className="flex justify-between">
                                <div>
                                  <Link to={`/contests/${contest.id}`} className="text-indigo-600 hover:text-indigo-900 font-medium">
                                    {contest.title}
                                  </Link>
                                  <div className="flex mt-1 space-x-2">
                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                      contest.status === 'open' ? 'bg-green-100 text-green-800' :
                                      contest.status === 'evaluation' ? 'bg-yellow-100 text-yellow-800' :
                                       'bg-blue-100 text-blue-800'
                                    }`}>
                                      {contest.status && typeof contest.status === 'string' 
                                        ? contest.status.charAt(0).toUpperCase() + contest.status.slice(1) 
                                        : 'Unknown'}
                                    </span>
                                    {contest.status === 'evaluation' && (
                                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                        Needs Judging
                                      </span>
                                    )}
                                  </div>
                                </div>
                                <Link 
                                  to={`/contests/${contest.id}`} 
                                  className={`text-sm font-medium ${contest.status === 'evaluation' ? 'text-red-600 hover:text-red-900' : 'text-gray-500'}`}
                                >
                                  {contest.status === 'evaluation' ? 'Judge Now' : 'View'}
                                </Link>
                              </div>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : (
                      <p className="text-gray-500 italic">Not participating in any contests as a judge.</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'credits' && (
            <div>
              <h2 className="text-xl font-medium mb-4">Credits Management</h2>
              <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
                <h3 className="font-medium text-gray-700">Current Balance</h3>
                <p className="text-2xl font-bold text-indigo-600">
                  {user?.credits !== undefined ? `${user.credits} credits` : 'Loading...'}
                </p>
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
          password: selectedContest.password || undefined,
          end_date: selectedContest.end_date || undefined,
          judge_restrictions: selectedContest.judge_restrictions,
          author_restrictions: selectedContest.author_restrictions,
          min_votes_required: selectedContest.min_votes_required,
          status: selectedContest.status,
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
          is_public: selectedAgent.is_public
        } : undefined}
        isEditing={isEditing}
        isAdmin={user?.is_admin}
      />

      {/* Submissions Modal */}
      {isSubmissionsModalOpen && selectedContestForSubmissions && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl transform transition-all sm:max-w-4xl sm:w-full max-h-[90vh] flex flex-col">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-xl font-semibold text-gray-800">
                Submissions for: {typeof selectedContestForSubmissions.title === 'string' ? selectedContestForSubmissions.title : 'Selected Contest'}
              </h3>
            </div>
            
            <div className="px-6 py-4 overflow-y-auto flex-grow">
              {isLoadingSubmissions ? (
                <div className="flex justify-center items-center h-32">
                  <svg className="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
              ) : submissionsForSelectedContest.length === 0 ? (
                <p className="text-gray-500 text-center py-10">No submissions found for this contest.</p>
              ) : (
                <div className="space-y-4">
                  {submissionsForSelectedContest.map((submission) => (
                    <div key={submission.id} className="p-4 border border-gray-200 rounded-md shadow-sm bg-white">
                      <h4 className="text-md font-semibold text-indigo-700 mb-1">{submission.title || 'Untitled Submission'}</h4>
                      <p className="text-xs text-gray-500 mb-1">
                        Author: <span className="font-medium text-gray-700">
                          {typeof submission.author === 'string' ? submission.author : (submission.author?.username || 'N/A')}
                        </span>
                        {/* Backend needs to provide owner username if different and required */}
                        {/* <span className="ml-2">Owner ID: {submission.owner_id || 'N/A'}</span> */}
                      </p>
                      <p className="text-xs text-gray-500 mb-2">
                        Submitted: {new Date(submission.submission_date).toLocaleString()}
                      </p>
                      <p className="text-sm text-gray-600 line-clamp-3 mb-3">
                        {submission.content}
                      </p>
                      <div className="flex items-center space-x-2">
                        <button 
                          onClick={() => handleOpenFullContentModal(submission)}
                          className="px-3 py-1 text-xs font-medium text-white bg-blue-500 rounded-md hover:bg-blue-600 transition-colors"
                        >
                          Read Full Content
                        </button>
                        <button 
                          onClick={() => handleRemoveSubmission(submission.id)}
                          className="px-3 py-1 text-xs font-medium text-white bg-red-500 rounded-md hover:bg-red-600 disabled:opacity-50 transition-colors"
                          disabled={isRemovingSubmissionId === submission.id}
                        >
                          {isRemovingSubmissionId === submission.id ? 'Removing...' : 'Remove Submission'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 flex justify-end">
              <button
                type="button"
                onClick={handleCloseSubmissionsModal}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Full Submission Content Modal (Nested inside DashboardPage return) */}
      {isFullContentModalOpen && selectedSubmissionForContent && (
        <FullTextModal
          isOpen={isFullContentModalOpen}
          onClose={handleCloseFullContentModal}
          title={selectedSubmissionForContent.title || 'Submission Content'}
          content={selectedSubmissionForContent.content}
          author={typeof selectedSubmissionForContent.author === 'string' 
            ? selectedSubmissionForContent.author 
            : selectedSubmissionForContent.author?.username
          }
        />
      )}

      {/* Judge Management Modal */}
      {isJudgeModalOpen && selectedContestForJudges && (
        <JudgeManagementModal
          isOpen={isJudgeModalOpen}
          onClose={() => {
            setIsJudgeModalOpen(false);
            setSelectedContestForJudges(null);
          }}
          contestId={selectedContestForJudges.id}
          contestTitle={selectedContestForJudges.title}
          judgeRestrictions={selectedContestForJudges.judge_restrictions}
        />
      )}
    </div>
  );
};

export default DashboardPage; 