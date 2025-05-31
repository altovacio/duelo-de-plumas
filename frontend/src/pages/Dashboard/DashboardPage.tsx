import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useAuthStore } from '../../store/authStore';
import TextFormModal from '../../components/TextEditor/TextFormModal';
import ContestFormModal from '../../components/Contest/ContestFormModal';
import AgentFormModal from '../../components/Agent/AgentFormModal';
import WelcomeModal from '../../components/Onboarding/WelcomeModal';
import OverviewTab from '../../components/Dashboard/OverviewTab';
import ParticipationTab from '../../components/Dashboard/ParticipationTab';
import ErrorDisplay from '../../components/shared/ErrorDisplay';
import Pagination from '../../components/shared/Pagination';
import { getUserTexts, createText, updateText, deleteText, Text as TextType } from '../../services/textService';
import { getUserContests, createContest, updateContest, deleteContest, Contest as ContestType, getContestSubmissions, ContestText as ContestSubmissionType, removeSubmissionFromContest, getAuthorParticipation, getJudgeParticipation, getMemberParticipation, getContestMembers, addMemberToContest, removeMemberFromContest, ContestMember } from '../../services/contestService';
import { getAgents, createAgent, updateAgent, deleteAgent, Agent as AgentType } from '../../services/agentService';
import { getDashboardData } from '../../services/dashboardService';
import { toast } from 'react-hot-toast';
import { Link, useSearchParams } from 'react-router-dom';

import JudgeManagementModal from '../../components/Contest/JudgeManagementModal';

import FullTextModal from '../../components/Common/FullTextModal';

import { getUserCreditTransactions, type CreditTransaction } from '../../services/creditService';
import UserSearch from '../../components/shared/UserSearch';
import { User } from '../../services/userService';

type TabType = 'overview' | 'contests' | 'texts' | 'agents' | 'participation' | 'credits';

// Simple loading spinner component
const LoadingSpinner: React.FC = () => (
  <div className="flex justify-center items-center h-32">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
  </div>
);

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { isFirstLogin, setIsFirstLogin } = useAuthStore();
  const [searchParams, setSearchParams] = useSearchParams();
  const [showWelcomeModal, setShowWelcomeModal] = useState(false);

  // Initialize activeTab from URL parameter or default to 'overview'
  const getInitialTab = (): TabType => {
    const tabParam = searchParams.get('tab');
    const validTabs: TabType[] = ['overview', 'contests', 'texts', 'agents', 'participation', 'credits'];
    return validTabs.includes(tabParam as TabType) ? (tabParam as TabType) : 'overview';
  };
  
  const [activeTab, setActiveTab] = useState<TabType>(getInitialTab());
  
  // Function to handle tab changes and update URL
  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    // Reset pagination when switching tabs
    setCurrentPage(1);
    // Update URL parameter
    const newSearchParams = new URLSearchParams(searchParams);
    if (tab === 'overview') {
      newSearchParams.delete('tab'); // Remove tab param for default tab
    } else {
      newSearchParams.set('tab', tab);
    }
    setSearchParams(newSearchParams, { replace: true });
  };
  
  // Listen for URL parameter changes (e.g., browser back/forward)
  useEffect(() => {
    const newTab = getInitialTab();
    if (newTab !== activeTab) {
      setActiveTab(newTab);
    }
  }, [searchParams]);
  
  // Common state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [totalItems, setTotalItems] = useState(0);
  
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
  const [contestSubmissions, setContestSubmissions] = useState<ContestSubmissionType[]>([]);
  const [isLoadingSubmissions, setIsLoadingSubmissions] = useState(false);
  const [selectedSubmissionForModal, setSelectedSubmissionForModal] = useState<ContestSubmissionType | null>(null);
  const [showFullSubmissionModal, setShowFullSubmissionModal] = useState(false);
  
  // State for full text modal
  const [selectedTextForFullModal, setSelectedTextForFullModal] = useState<TextType | null>(null);
  const [showFullTextModal, setShowFullTextModal] = useState(false);
  
  // State for submission management
  const [, setErrorSubmissions] = useState<string | null>(null);
  const [isRemovingSubmissionId, setIsRemovingSubmissionId] = useState<number | null>(null);
  
  // Agent state
  const [isAgentModalOpen, setIsAgentModalOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<AgentType | null>(null);
  const [ownedAgentsData, setOwnedAgentsData] = useState<AgentType[]>([]);
  // Remove unused public agents state since it's not being used in this page
  // const [publicAgentsData, setPublicAgentsData] = useState<AgentType[]>([]);
  // const [isLoadingPublic, setIsLoadingPublic] = useState(false);
  
  // Editing flags
  const [isEditing, setIsEditing] = useState(false);

  // Add at the top with other state definitions:
  const [participationContests, setParticipationContests] = useState<{
    asAuthor: ContestType[];
    asJudge: ContestType[];
    asMember: ContestType[];
  }>({ asAuthor: [], asJudge: [], asMember: [] });
  const [isLoadingParticipation, setIsLoadingParticipation] = useState(false);

  // Add the following state variables in the component after other state definitions
  const [isJudgeModalOpen, setIsJudgeModalOpen] = useState(false);
  const [selectedContestForJudges, setSelectedContestForJudges] = useState<ContestType | null>(null);
  
  // Add the following state variables for text search
  const [textSearchQuery, setTextSearchQuery] = useState('');
  const [filteredTexts, setFilteredTexts] = useState<TextType[]>([]);
  const [isCreateTextDropdownOpen, setIsCreateTextDropdownOpen] = useState(false);

  // Dashboard data state
  const [dashboardData, setDashboardData] = useState<any>(null);

  // Transaction history state
  const [transactions, setTransactions] = useState<CreditTransaction[]>([]);
  const [isLoadingTransactions, setIsLoadingTransactions] = useState(false);
  const [transactionError, setTransactionError] = useState<string | null>(null);

  // State for member management modal
  const [isMemberModalOpen, setIsMemberModalOpen] = useState(false);
  const [selectedContestForMembers, setSelectedContestForMembers] = useState<ContestType | null>(null);
  const [contestMembers, setContestMembers] = useState<ContestMember[]>([]);
  const [isLoadingMembers, setIsLoadingMembers] = useState(false);
  const [memberError, setMemberError] = useState<string | null>(null);

  // Handle welcome modal for first-time users
  useEffect(() => {
    if (isFirstLogin && user) {
      setShowWelcomeModal(true);
    }
  }, [isFirstLogin, user]);

  const handleCloseWelcomeModal = () => {
    setShowWelcomeModal(false);
    setIsFirstLogin(false);
  };

  // Define all functions before useEffects that call them
  
  // Text management functions
  const fetchTexts = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const skip = (currentPage - 1) * itemsPerPage;
      
      // Pass search query to server-side search
      const searchQuery = textSearchQuery.trim() || undefined;
      const texts = await getUserTexts(skip, itemsPerPage, searchQuery);
      setTextsData(texts);
      setFilteredTexts(texts); // No longer needed since search is server-side, but keeping for compatibility
      
      // Simple logic: if we got a full page, there might be more
      if (texts.length === itemsPerPage) {
        setTotalItems((currentPage * itemsPerPage) + 1); // +1 to indicate there might be more
      } else {
        setTotalItems(skip + texts.length); // Exact count
      }
    } catch (err) {
      console.error('Error fetching texts:', err);
      setError('Failed to load texts. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  // Contest management functions
  const fetchContests = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const skip = (currentPage - 1) * itemsPerPage;
      
      const contests = await getUserContests(skip, itemsPerPage);
      setContestsData(contests);
      
      // Simple pagination logic
      if (contests.length === itemsPerPage) {
        setTotalItems((currentPage * itemsPerPage) + 1);
      } else {
        setTotalItems(skip + contests.length);
      }
      
    } catch (err) {
      console.error('Error fetching contests:', err);
      setError('Failed to load contests. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  // Agent management functions
  const fetchAgents = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const skip = (currentPage - 1) * itemsPerPage;
      const ownedAgents = await getAgents(false, skip, itemsPerPage);
      setOwnedAgentsData(ownedAgents);
      
      // Simple logic: if we got a full page, there might be more
      if (ownedAgents.length === itemsPerPage) {
        setTotalItems((currentPage * itemsPerPage) + 1); // +1 to indicate there might be more
      } else {
        setTotalItems(skip + ownedAgents.length); // Exact count
      }
    } catch (err) {
      console.error('Error fetching agents:', err);
      setError('Failed to load agents. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  // Dashboard overview data
  const fetchOverviewData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const dashboardDataResponse = await getDashboardData();
      setDashboardData(dashboardDataResponse);
      
      // Update contests data if available
      if (dashboardDataResponse.author_contests) {
        setContestsData(dashboardDataResponse.author_contests);
      }
      
      // Fetch texts with reasonable limit for overview count (not paginated)
      try {
        const allTexts = await getUserTexts(0, 100); // Get up to 100 texts for overview count
        setTextsData(allTexts);
      } catch (textError) {
        console.warn('Could not fetch all texts for overview:', textError);
        // Fallback to regular paginated fetch
        fetchTexts();
      }
      
      // Fetch agents with a reasonable limit for overview (not paginated)
      try {
        const allAgents = await getAgents(false, 0, 100); // Use reasonable limit that backend accepts
        setOwnedAgentsData(allAgents);
      } catch (agentError) {
        console.warn('Could not fetch all agents for overview:', agentError);
        // Fallback to regular paginated fetch
        fetchAgents();
      }
      
      setIsLoading(false);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data. Please try again later.');
      setIsLoading(false);
    }
  };

  // Add this function to fetch participation data
  const fetchParticipation = async () => {
    try {
      setIsLoadingParticipation(true);
      setError(null);
      
      const [asAuthor, asJudge, asMember, createdContests] = await Promise.all([
        getAuthorParticipation(),
        getJudgeParticipation(),
        getMemberParticipation(),
        getUserContests(0, 100) // Fetch created contests independently
      ]);
      
      setParticipationContests({ asAuthor, asJudge, asMember });
      setContestsData(createdContests); // Update contests data for "Contests I created" column
      
      // Don't calculate total items for pagination since we're showing all data
    } catch (err) {
      console.error('Error fetching participation:', err);
      setError('Failed to load participation data. Please try again later.');
    } finally {
      setIsLoadingParticipation(false);
    }
  };

  const fetchTransactions = async () => {
    try {
      setIsLoadingTransactions(true);
      setTransactionError(null);
      const skip = (currentPage - 1) * itemsPerPage;
      const transactionData = await getUserCreditTransactions(skip, itemsPerPage);
      setTransactions(transactionData);
      
      // Simple logic: if we got a full page, there might be more
      if (transactionData.length === itemsPerPage) {
        setTotalItems((currentPage * itemsPerPage) + 1); // +1 to indicate there might be more
      } else {
        setTotalItems(skip + transactionData.length); // Exact count
      }
    } catch (err: any) {
      console.error('Error fetching transactions:', err);
      setTransactionError('Failed to load transaction history');
    } finally {
      setIsLoadingTransactions(false);
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

  // Add function to handle opening the member management modal
  const handleOpenMemberManagementModal = async (contest: ContestType) => {
    setSelectedContestForMembers(contest);
    setIsMemberModalOpen(true);
    setIsLoadingMembers(true);
    setMemberError(null);
    try {
      const members = await getContestMembers(contest.id);
      setContestMembers(members);
    } catch (err) {
      console.error('Error fetching members:', err);
      setMemberError('Failed to load members. Please try again later.');
      setContestMembers([]);
    } finally {
      setIsLoadingMembers(false);
    }
  };

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
      // Fetch transaction history for credits tab
      fetchTransactions();
    }
  }, [activeTab]); // Removed currentPage dependency for client-side paginated sections

  // Separate effect for server-side paginated sections
  useEffect(() => {
    if (activeTab === 'texts') {
      fetchTexts();
    } else if (activeTab === 'contests') {
      fetchContests();
    } else if (activeTab === 'agents') {
      fetchAgents();
    } else if (activeTab === 'credits') {
      fetchTransactions();
    }
    // Note: participation uses client-side pagination, so no server call needed on page change
  }, [currentPage]); // Only refetch server-side paginated data when page changes

  // Handle text search changes - reset to page 1 and fetch new results
  useEffect(() => {
    if (activeTab === 'texts') {
      setCurrentPage(1); // Reset to first page when searching
      fetchTexts();
    }
  }, [textSearchQuery]); // Trigger when search query changes

  // Helper function to refresh user data

  // Text management functions (remaining handlers)
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

  const handleOpenTextFullModal = (text: TextType) => {
    setSelectedTextForFullModal(text);
    setShowFullTextModal(true);
  };

  const handleCloseTextFullModal = () => {
    setShowFullTextModal(false);
    setSelectedTextForFullModal(null);
  };

  // Contest management functions (remaining handlers)
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
    password_protected: boolean;
    publicly_listed: boolean;
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

  // Agent management functions (remaining handlers)
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

  // Temporarily commented out since public agents section is disabled
  /*
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
  */

  const handleOpenSubmissionsModal = async (contest: ContestType) => {
    setSelectedContestForSubmissions(contest);
    setIsSubmissionsModalOpen(true);
    setIsLoadingSubmissions(true);
    setErrorSubmissions(null);
    try {
      const submissions = await getContestSubmissions(contest.id);
      setContestSubmissions(submissions);
    } catch (err) {
      console.error('Error fetching submissions:', err);
      setErrorSubmissions('Failed to load submissions. Please try again later.');
      setContestSubmissions([]); // Clear previous submissions on error
    } finally {
      setIsLoadingSubmissions(false);
    }
  };

  const handleCloseSubmissionsModal = () => {
    setIsSubmissionsModalOpen(false);
    setSelectedContestForSubmissions(null);
    setContestSubmissions([]);
    setIsLoadingSubmissions(false);
    setErrorSubmissions(null);
  };

  const handleOpenFullContentModal = (submission: ContestSubmissionType) => {
    setSelectedSubmissionForModal(submission);
    setShowFullSubmissionModal(true);
  };

  const handleCloseFullContentModal = () => {
    setShowFullSubmissionModal(false);
    setSelectedSubmissionForModal(null);
  };

  const handleRemoveSubmission = async (submissionId: number) => {
    if (!selectedContestForSubmissions) return;

    const submissionToRemove = contestSubmissions.find(s => s.id === submissionId);
    if (!submissionToRemove) return;

    if (!window.confirm(`Are you sure you want to remove the submission "${submissionToRemove.title || 'Untitled Submission'}"? This action cannot be undone.`)) {
      return;
    }

    setIsRemovingSubmissionId(submissionId);
    try {
      await removeSubmissionFromContest(selectedContestForSubmissions.id, submissionId);
      // Refresh the list
      const updatedSubmissions = await getContestSubmissions(selectedContestForSubmissions.id);
      setContestSubmissions(updatedSubmissions);
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

  // Add member to contest
  const handleAddMember = async (user: User | null) => {
    if (!selectedContestForMembers || !user) return;
    
    try {
      setIsLoadingMembers(true);
      setMemberError(null);
      
      const newMember = await addMemberToContest(selectedContestForMembers.id, user.id);
      setContestMembers([...contestMembers, newMember]);
      toast.success('Member added successfully');
    } catch (err: any) {
      console.error('Error adding member:', err);
      setMemberError(err.message || 'Failed to add member. Please try again.');
    } finally {
      setIsLoadingMembers(false);
    }
  };

  // Remove member from contest
  const handleRemoveMember = async (userId: number) => {
    if (!selectedContestForMembers) return;
    
    if (window.confirm('Are you sure you want to remove this member from the contest?')) {
      try {
        setIsLoadingMembers(true);
        setMemberError(null);
        
        await removeMemberFromContest(selectedContestForMembers.id, userId);
        setContestMembers(contestMembers.filter(member => member.user_id !== userId));
        toast.success('Member removed successfully');
      } catch (err: any) {
        console.error('Error removing member:', err);
        setMemberError('Failed to remove member. Please try again.');
      } finally {
        setIsLoadingMembers(false);
      }
    }
  };

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

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
              onClick={() => handleTabChange('overview')}
            >
              Overview
            </button>
            <button 
              className={tabClasses('contests')}
              onClick={() => handleTabChange('contests')}
            >
              My Contests
            </button>
            <button 
              className={tabClasses('texts')}
              onClick={() => handleTabChange('texts')}
            >
              My Texts
            </button>
            <button 
              className={tabClasses('agents')}
              onClick={() => handleTabChange('agents')}
            >
              AI Agents
            </button>
            <button 
              className={tabClasses('participation')}
              onClick={() => handleTabChange('participation')}
            >
              Participation
            </button>
            <button 
              className={tabClasses('credits')}
              onClick={() => handleTabChange('credits')}
            >
              Credits
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div>
          {activeTab === 'overview' && (
            <OverviewTab 
              dashboardData={dashboardData}
              textsCount={textsData.length}
              contestsCount={contestsData.length}
              agentsCount={ownedAgentsData.length}
            />
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
                <ErrorDisplay error={error} />
              )}
              
              {isLoading ? (
                <LoadingSpinner />
              ) : contestsData.length > 0 ? (
                <div>
                  <div className="space-y-4">
                    {contestsData.map((contest) => (
                      <div key={contest.id} className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                        <div className="p-6">
                          {/* Header */}
                          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-4">
                            <div className="flex-1 min-w-0">
                              <Link 
                                to={`/contests/${contest.id}`}
                                className="text-lg font-medium text-indigo-600 hover:text-indigo-900 hover:underline block truncate"
                              >
                                {contest.title}
                              </Link>
                              <div className="flex flex-wrap gap-2 mt-2">
                                {/* Status Badge */}
                                <select
                                  value={contest.status}
                                  onChange={(e) => handleStatusChange(contest.id, e.target.value as 'open' | 'evaluation' | 'closed')}
                                  className="px-3 py-1 rounded-full text-xs font-medium border border-gray-300 bg-white text-gray-800 cursor-pointer"
                                  style={{
                                    backgroundColor: contest.status === 'open' ? '#dcfce7' : 
                                                   contest.status === 'evaluation' ? '#fef3c7' : '#dbeafe',
                                    color: contest.status === 'open' ? '#166534' :
                                           contest.status === 'evaluation' ? '#92400e' : '#1e40af'
                                  }}
                                >
                                  <option value="open">Open</option>
                                  <option value="evaluation">Evaluation</option>
                                  <option value="closed">Closed</option>
                                </select>
                                
                                {/* Type Badge */}
                                <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                                  contest.publicly_listed ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'
                                }`}>
                                  {contest.publicly_listed ? 'Public' : 'Private'}
                                </span>
                                
                                {/* Password Protection Badge */}
                                {contest.password_protected && (
                                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                    🔒 Password Protected
                                  </span>
                                )}
                              </div>
                            </div>
                            
                            {/* Quick Stats */}
                            <div className="flex flex-col sm:items-end mt-4 sm:mt-0 sm:ml-4">
                              <div className="text-sm text-gray-500 mb-1">
                                <span className="font-medium">{contest.participant_count || 0}</span> participants
                              </div>
                              <div className="text-sm text-gray-500">
                                Created {new Date(contest.created_at).toLocaleDateString()}
                              </div>
                            </div>
                          </div>
                          
                          {/* Actions */}
                          <div className="border-t border-gray-200 pt-4">
                            <div className="flex flex-wrap gap-2">
                              <button 
                                onClick={() => handleOpenEditContestModal(contest)}
                                className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                              >
                                <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                                Edit
                              </button>
                              
                              <button 
                                onClick={() => handleOpenSubmissionsModal(contest)}
                                className="inline-flex items-center px-3 py-1.5 border border-green-300 text-sm font-medium rounded-md text-green-700 bg-green-50 hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                              >
                                <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                View Submissions
                              </button>
                              
                              <button 
                                onClick={() => handleOpenJudgeManagementModal(contest)}
                                className="inline-flex items-center px-3 py-1.5 border border-blue-300 text-sm font-medium rounded-md text-blue-700 bg-blue-50 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                              >
                                <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                                </svg>
                                Manage Judges
                              </button>
                              
                              {!contest.publicly_listed && (
                                <button 
                                  onClick={() => handleOpenMemberManagementModal(contest)}
                                  className="inline-flex items-center px-3 py-1.5 border border-purple-300 text-sm font-medium rounded-md text-purple-700 bg-purple-50 hover:bg-purple-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                                >
                                  <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                                  </svg>
                                  Manage Members
                                </button>
                              )}
                              
                              <button 
                                onClick={() => handleDeleteContest(contest.id)}
                                className="inline-flex items-center px-3 py-1.5 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-red-50 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                              >
                                <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                                Delete
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {/* Pagination */}
                  {totalItems > itemsPerPage && (
                    <Pagination
                      currentPage={currentPage}
                      totalItems={totalItems}
                      itemsPerPage={itemsPerPage}
                      onPageChange={handlePageChange}
                      className="mt-6"
                    />
                  )}
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
                <ErrorDisplay error={error} />
              )}
              
              {isLoading ? (
                <LoadingSpinner />
              ) : filteredTexts.length > 0 ? (
                <div>
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
                              <button
                                onClick={() => handleOpenTextFullModal(text)}
                                className="text-indigo-600 hover:text-indigo-900 hover:underline text-left"
                              >
                                {text.title}
                              </button>
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
                  
                  {/* Pagination */}
                  {totalItems > itemsPerPage && (
                    <Pagination
                      currentPage={currentPage}
                      totalItems={totalItems}
                      itemsPerPage={itemsPerPage}
                      onPageChange={handlePageChange}
                      className="mt-6"
                    />
                  )}
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
                <ErrorDisplay error={error} />
              )}
              <div className="mb-8">
                <h3 className="text-lg font-medium text-gray-800 mb-4">My Agents</h3>
                {isLoading ? (
                  <LoadingSpinner />
                ) : ownedAgentsData.length > 0 ? (
                  <div>
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
                    
                    {/* Pagination for My Agents */}
                    {totalItems > itemsPerPage && (
                      <Pagination
                        currentPage={currentPage}
                        totalItems={totalItems}
                        itemsPerPage={itemsPerPage}
                        onPageChange={handlePageChange}
                        className="mt-6"
                      />
                    )}
                  </div>
                ) : (
                  <p className="text-gray-500 italic">You haven't created any AI agents yet.</p>
                )}
              </div>
              {/* Temporary removal of public agents section until it's properly implemented
              <div>
                <h3 className="text-lg font-medium text-gray-800 mb-4">Public Agents</h3>
                {isLoadingPublic ? (
                  <div className="flex justify-center items-center h-32">
                    <svg className="animate-spin h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 8 18-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 7 14 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
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
              */}
            </div>
          )}

          {activeTab === 'participation' && (
            <ParticipationTab 
              contestsData={contestsData}
              participationContests={participationContests}
              isLoading={isLoadingParticipation}
              error={error}
            />
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
              
              <h3 className="font-medium text-gray-700 mb-4">Transaction History</h3>
              
              {transactionError && (
                <ErrorDisplay error={transactionError} />
              )}
              
              {isLoadingTransactions ? (
                <LoadingSpinner />
              ) : transactions.length > 0 ? (
                <div>
                  <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                    <table className="min-w-full divide-y divide-gray-300">
                      <thead className="bg-gray-50">
                        <tr>
                          <th scope="col" className="py-3 pl-4 pr-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Date</th>
                          <th scope="col" className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Type</th>
                          <th scope="col" className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Amount</th>
                          <th scope="col" className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Description</th>
                          <th scope="col" className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">AI Model</th>
                          <th scope="col" className="px-3 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">Tokens</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200 bg-white">
                        {transactions.map((transaction) => (
                          <tr key={transaction.id}>
                            <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm text-gray-900">
                              {new Date(transaction.created_at).toLocaleString()}
                            </td>
                            <td className="px-3 py-4 text-sm">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                transaction.transaction_type === 'purchase' ? 'bg-green-100 text-green-800' :
                                transaction.transaction_type === 'refund' ? 'bg-blue-100 text-blue-800' :
                                transaction.transaction_type === 'admin_adjustment' ? 'bg-purple-100 text-purple-800' :
                                'bg-red-100 text-red-800'
                              }`}>
                                {transaction.transaction_type === 'purchase' ? 'Purchase' :
                                 transaction.transaction_type === 'consumption' ? 'Consumption' :
                                 transaction.transaction_type === 'refund' ? 'Refund' :
                                 'Admin Adjustment'}
                              </span>
                            </td>
                            <td className="px-3 py-4 text-sm font-medium">
                              <span className={transaction.amount >= 0 ? 'text-green-600' : 'text-red-600'}>
                                {transaction.amount >= 0 ? '+' : ''}{transaction.amount}
                              </span>
                            </td>
                            <td className="px-3 py-4 text-sm text-gray-900">{transaction.description}</td>
                            <td className="px-3 py-4 text-sm text-gray-500">
                              {transaction.ai_model || '-'}
                            </td>
                            <td className="px-3 py-4 text-sm text-gray-500">
                              {transaction.tokens_used ? transaction.tokens_used.toLocaleString() : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Pagination */}
                  {totalItems > itemsPerPage && (
                    <Pagination
                      currentPage={currentPage}
                      totalItems={totalItems}
                      itemsPerPage={itemsPerPage}
                      onPageChange={handlePageChange}
                      className="mt-6"
                    />
                  )}
                </div>
              ) : (
                <div className="text-center py-12">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No transactions</h3>
                  <p className="mt-1 text-sm text-gray-500">You haven't made any credit transactions yet.</p>
                </div>
              )}
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
          password_protected: selectedContest.password_protected,
          publicly_listed: selectedContest.publicly_listed,
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
                <LoadingSpinner />
              ) : contestSubmissions.length === 0 ? (
                <p className="text-gray-500 text-center py-10">No submissions found for this contest.</p>
              ) : (
                <div className="space-y-4">
                  {contestSubmissions.map((submission) => (
                    <div key={submission.id} className="p-4 border border-gray-200 rounded-md shadow-sm bg-white">
                      <h4 className="text-md font-semibold text-indigo-700 mb-1">{submission.title || 'Untitled Submission'}</h4>
                      <p className="text-xs text-gray-500 mb-1">
                        Author: <span className="font-medium text-gray-700">
                          {typeof submission.author === 'string' ? submission.author : (submission.author?.username || 'N/A')}
                        </span>
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

      {/* Full Submission Content Modal */}
      {showFullSubmissionModal && selectedSubmissionForModal && (
        <FullTextModal
          isOpen={showFullSubmissionModal}
          onClose={handleCloseFullContentModal}
          title={selectedSubmissionForModal.title || 'Submission Content'}
          content={selectedSubmissionForModal.content}
          author={typeof selectedSubmissionForModal.author === 'string' 
            ? selectedSubmissionForModal.author 
            : selectedSubmissionForModal.author?.username
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
        />
      )}

      {/* Full Text Modal for My Texts */}
      {showFullTextModal && selectedTextForFullModal && (
        <FullTextModal
          isOpen={showFullTextModal}
          onClose={handleCloseTextFullModal}
          title={selectedTextForFullModal.title}
          content={selectedTextForFullModal.content}
          author={selectedTextForFullModal.author}
        />
      )}

      {/* Member Management Modal */}
      {isMemberModalOpen && selectedContestForMembers && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl transform transition-all sm:max-w-2xl sm:w-full max-h-[90vh] flex flex-col">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-xl font-semibold text-gray-800">
                Manage Members: {selectedContestForMembers.title}
              </h3>
            </div>
            
            <div className="px-6 py-4 overflow-y-auto flex-grow">
              {memberError && (
                <ErrorDisplay error={memberError} />
              )}

              {/* Add Member Section */}
              <div className="mb-6">
                <h4 className="text-lg font-medium text-gray-900 mb-3">Add New Member</h4>
                <p className="text-sm text-gray-500 mb-4">
                  Search for users by username or email to add them as members for this contest.
                </p>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Search Users
                  </label>
                  <UserSearch
                    onUserSelect={handleAddMember}
                    placeholder="Type username or email..."
                  />
                </div>
              </div>

              {/* Current Members List */}
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-3">Current Members</h4>
                {isLoadingMembers ? (
                  <LoadingSpinner />
                ) : contestMembers.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No members found for this contest.</p>
                ) : (
                  <div className="space-y-3">
                    {contestMembers.map((member) => (
                      <div key={member.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-md">
                        <div>
                          <p className="font-medium text-gray-900">{member.username}</p>
                          <p className="text-sm text-gray-500">
                            Added: {new Date(member.added_at).toLocaleDateString()}
                          </p>
                        </div>
                        <button
                          onClick={() => handleRemoveMember(member.user_id)}
                          disabled={isLoadingMembers}
                          className="px-3 py-1 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 flex justify-end">
              <button
                type="button"
                onClick={() => {
                  setIsMemberModalOpen(false);
                  setSelectedContestForMembers(null);
                  setMemberError(null);
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Welcome Modal for first-time users */}
      <WelcomeModal 
        isOpen={showWelcomeModal}
        onClose={handleCloseWelcomeModal}
        isFirstLogin={isFirstLogin}
      />
    </div>
  );
};

export default DashboardPage; 