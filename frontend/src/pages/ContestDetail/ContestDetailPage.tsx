import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import * as contestService from '../../services/contestService';
import TextSubmissionForm from '../../components/Contest/TextSubmissionForm';
import HumanJudgingForm from '../../components/Contest/HumanJudgingForm';
import AIJudgeExecutionForm from '../../components/Contest/AIJudgeExecutionForm';
import ContestResults from '../../components/Contest/ContestResults';
import { toast } from 'react-hot-toast';
import { getAgents, Agent } from '../../services/agentService';
import { getJudgeVotes } from '../../services/voteService';
// import MarkdownEditor from '../../components/MarkdownEditor'; // Commented out - not yet developed
// import TextSelectionModal from '../../components/TextSelectionModal'; // Commented out - not yet developed
// import JudgingForm from '../../components/Contest/JudgingForm'; // Commented out - not yet developed

// Use the Contest type from the service, potentially extended if needed locally
// For now, assume ContestServiceType is sufficient, but we need to handle 'creator' if it's different.
// The service defines `creator_id`, but this page expects a `creator` object.
// This implies the actual response for getContest might be richer than the generic ContestServiceType.
// We'll define a local type that reflects what this page *expects* getContest to return,
// aligning fields with ContestServiceType where possible.

interface ContestPageSpecificData extends Omit<contestService.Contest, 'creator_id' | 'updated_at' | 'is_private' | 'has_password' | 'min_votes_required'> {
  full_description?: string; // Markdown content, specific to detail view
  creator: { // Assuming backend sends this nested object for this specific endpoint
    id: number;
    username: string;
  };
  last_modified: string; // Page uses last_modified, service has updated_at
  type: 'public' | 'private'; // Page uses type, service has is_private
  is_password_protected: boolean; // Page uses is_password_protected, service has has_password
  min_required_votes?: number; // Page uses min_required_votes, service has min_votes_required
  // participant_count and text_count are already fine (snake_case in both)
}

// Text interface for local use in this component (separate from the service)
interface ContestText {
  id: number;
  title: string;
  content: string; // Markdown content
  author?: {
    id: number;
    username: string;
  };
  owner?: {
    id: number;
    username: string;
  };
  created_at: string;
  updated_at?: string; // Add updated_at, can be same as created_at if not available from submission
  votes?: {
    rank: number;
    judge: {
      id: number;
      username: string;
      isAI: boolean;
      aiModel?: string;
    };
    comment: string;
  }[];
}

const ContestDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const { isAuthenticated, user } = useAuth();
    const [contest, setContest] = useState<ContestPageSpecificData | null>(null);
    const [texts, setTexts] = useState<contestService.ContestText[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [password, setPassword] = useState<string>('');
    const [isPasswordCorrect, setIsPasswordCorrect] = useState<boolean>(false);
    const [passwordError, setPasswordError] = useState<string | null>(null);
    const [showPasswordModal, setShowPasswordModal] = useState<boolean>(false);
    const fetchInitiatedForCurrentId = useRef(false);
    const [isFetching, setIsFetching] = useState(false);
    
    // States for modal dialogs
    const [showSubmitTextModal, setShowSubmitTextModal] = useState<boolean>(false);
    const [showJudgeModal, setShowJudgeModal] = useState<boolean>(false);
    const [showAIJudgeModal, setShowAIJudgeModal] = useState<boolean>(false);
    const [isJudge, setIsJudge] = useState<boolean>(false);
    const [averageTextLength, setAverageTextLength] = useState<number>(1000); // Default estimate
    const [showFullTextModal, setShowFullTextModal] = useState<boolean>(false);
    const [selectedTextForModal, setSelectedTextForModal] = useState<contestService.ContestText | null>(null);

    // New states for managing user's specific submissions and withdrawal process
    const [userSubmissions, setUserSubmissions] = useState<contestService.ContestText[]>([]);
    const [isProcessingWithdrawal, setIsProcessingWithdrawal] = useState<number | null>(null);

    // New state for admin/creator withdrawal processing
    const [isProcessingAdminWithdrawal, setIsProcessingAdminWithdrawal] = useState<number | null>(null);

    // New state for submission success message
    const [submissionStatusMessage, setSubmissionStatusMessage] = useState<string | null>(null);

    // Add state for available judge agents
    const [availableJudgeAgents, setAvailableJudgeAgents] = useState<Agent[]>([]);
    const [isLoadingJudgeAgents, setIsLoadingJudgeAgents] = useState(false);

    // Add state for more detailed voting status
    const [judgeCompletionStatus, setJudgeCompletionStatus] = useState<{
      totalJudges: number;
      completedJudges: number;
      userHasJudged: boolean;
      judgeDetails: { name: string; type: 'human' | 'ai'; completed: boolean; }[];
      isLoading: boolean;
    }>({
      totalJudges: 0,
      completedJudges: 0,
      userHasJudged: false,
      judgeDetails: [],
      isLoading: false
    });

  const fetchContestDetails = async (passwordAttemptFromForm?: string) => {
    console.log('Fetching contest details');
    if (!id) {
      return;
    }
    setIsLoading(true);

    // Determine which password to use for the API request
    let passwordForApi: string | undefined = passwordAttemptFromForm;
    if (passwordForApi === undefined && isPasswordCorrect) {
      passwordForApi = password; 
    }

    try {
      // Fetch main contest data
      const contestDataFromService = await contestService.getContest(parseInt(id), passwordForApi);
      console.log('API Response for getContest (contestDataFromService):', JSON.stringify(contestDataFromService, null, 2)); // Log the raw service response
      
      // Format contest data for the page
      const contestDataForPage: ContestPageSpecificData = {
        ...contestDataFromService,
        creator: contestDataFromService.creator || { id: contestDataFromService.creator_id, username: 'Unknown' }, 
        full_description: contestDataFromService.description, 
        last_modified: contestDataFromService.updated_at,
        type: contestDataFromService.is_private ? 'private' : 'public',
        is_password_protected: contestDataFromService.has_password,
        min_required_votes: contestDataFromService.min_votes_required,
        participant_count: contestDataFromService.participant_count || 0,
        text_count: contestDataFromService.text_count || 0,
      };
      setContest(contestDataForPage);
      setPasswordError(null);

      // Log the user object from useAuth() at the time of check
      console.log('User object from useAuth():', JSON.stringify(user, null, 2));

      // Determine if user has access to the contest
      const isCreator = user?.id === contestDataForPage.creator.id;
      console.log(`Determining isCreator: user?.id (${user?.id}) === contestDataForPage.creator.id (${contestDataForPage.creator.id}). Result: ${isCreator}`);
      const isAdmin = user?.is_admin;
      let grantAccess = false;
      let showPwModal = false;

      if (isCreator || isAdmin) {
        grantAccess = true;
      } else if (!contestDataForPage.is_password_protected) {
        grantAccess = true;
      } else if (passwordForApi !== undefined) {
        grantAccess = true;
        if (passwordAttemptFromForm !== undefined && passwordAttemptFromForm !== password) {
          setPassword(passwordAttemptFromForm);
        }
      } else {
        showPwModal = true;
      }

      setIsPasswordCorrect(grantAccess);
      setShowPasswordModal(showPwModal);

      // Reset state variables
      setTexts([]);
      setUserSubmissions([]);
      setIsJudge(false);

      if (grantAccess) {
        let actualPasswordToUseForSubCalls: string | undefined = undefined;
        if (contestDataForPage.is_password_protected) {
          actualPasswordToUseForSubCalls = passwordForApi !== undefined ? passwordForApi : password;
        }

        // Attempt to fetch submissions if user is authenticated
        if (isAuthenticated && user) {
          try {
            // Fetch current user's submissions regardless of contest status
            const mySubmissionsData = await contestService.getContestMySubmissions(parseInt(id));
            setUserSubmissions(mySubmissionsData);
          } catch (error) {
            console.warn('Failed to fetch user submissions:', error);
            setUserSubmissions([]);
          }

          // Determine if the user can view ALL submissions
          // This flag determines if we fetch the `texts` array (all submissions).
          // Creators will manage all submissions via the dashboard for 'open' contests.
          // For 'evaluation' or 'closed' contests, all submissions are typically viewable by participants/public.
          const canViewAllSubmissions = 
              contestDataForPage.status === 'evaluation' || contestDataForPage.status === 'closed';

          console.log(`Value of canViewAllSubmissions: ${canViewAllSubmissions}, Status: ${contestDataForPage.status}, isCreator: ${isCreator}`);

          if (canViewAllSubmissions) {
            try {
              console.log(`Attempting to fetch all submissions for contest ${id}`); // Log before API call
              const allSubmissionsData = await contestService.getContestSubmissions(parseInt(id), actualPasswordToUseForSubCalls);
              console.log('API Response for getContestSubmissions (allSubmissionsData):', JSON.stringify(allSubmissionsData, null, 2)); // Log the response
              setTexts(allSubmissionsData);
              
              if (allSubmissionsData.length > 0) {
                const totalLength = allSubmissionsData.reduce((sum, text) => sum + text.content.length, 0);
                setAverageTextLength(Math.ceil(totalLength / allSubmissionsData.length));
              }
            } catch (error) {
              console.warn('Failed to fetch all submissions:', error);
              setTexts([]);
            }
          } else {
            setTexts([]);
          }
        } else {
          setTexts([]);
          setUserSubmissions([]);
        }
        
        // Fetch judge status
        if (isAuthenticated && user) {
          try {
            const judges = await contestService.getContestJudges(parseInt(id));
            setIsJudge(judges.some(judge => judge.user_judge_id === user.id));
          } catch (error) {
            console.warn('Failed to fetch contest judges:', error);
            setIsJudge(false);
          }
        } else {
          setIsJudge(false);
        }
      } else {
        // Access not granted (password modal will be shown), clear sensitive secondary data
        console.log('v.11 Access not granted, clearing submissions and judge status.');
        setTexts([]);
        setIsJudge(false);
        setUserSubmissions([]); // Ensure cleared if access not granted
      }

      // Add this at the end of the fetchContestDetails function, right before the final setIsLoading(false)
      if (grantAccess && contestDataForPage.status === 'evaluation') {
        await fetchJudgeStatus(parseInt(id));
        // Check judge completion status for evaluation contests
        await checkJudgeCompletionStatus(parseInt(id));
      } else if (grantAccess && contestDataForPage.status === 'closed') {
        // Also check judge completion status for closed contests to show final status
        await checkJudgeCompletionStatus(parseInt(id));
      }

    } catch (err: any) {
      console.error('v.11 Error fetching main contest details (likely from getContest):', err);
      const isAxiosError = err.isAxiosError !== undefined;
      const status = isAxiosError ? err.response?.status : null;
      
      setContest(null); 
      setIsPasswordCorrect(false); // Definitely no access if main fetch failed

      if (status === 403) {
        setShowPasswordModal(true);
        if (passwordAttemptFromForm !== undefined) {
          setPasswordError('Incorrect password.');
        } else {
          setPasswordError('This contest requires a password or access is restricted.');
        }
      } else if (status === 401) { 
        setPasswordError('You are not authorized to view this contest.');
        setShowPasswordModal(false); // Not a password issue, but auth issue
      } else {
        setPasswordError('Failed to load contest details. Please try again.');
        setShowPasswordModal(false); // Generic error, hide password modal
      }
    } finally {
      setIsLoading(false);
      console.log('v.11 fetchContestDetails finished.');
    }
  };

  // Update the fetchJudgeStatus function to use user_judge_id
  const fetchJudgeStatus = async (contestId: number) => {
    if (!isAuthenticated || !user) {
      setIsJudge(false);
      return;
    }

    try {
      // Fetch contest judges to check if current user is a judge
      const judges = await contestService.getContestJudges(contestId);
      const userIsJudge = judges.some(judge => judge.user_judge_id === user.id);
      
      // Also consider creators as judges by default
      const isCreator = contest && user.id === contest.creator.id;
      
      setIsJudge(userIsJudge || isCreator || user.is_admin);
      
      console.log(`Judge status for contest ${contestId}:`, { 
        userIsJudge, 
        isCreator: isCreator || false, 
        isAdmin: user.is_admin || false,
        finalStatus: userIsJudge || isCreator || user.is_admin
      });
    } catch (err) {
      console.error('Error checking judge status:', err);
      // Don't set error state, just log the error to not disrupt the user experience
    }
  };

  useEffect(() => {
    console.log(`v.11 useEffect triggered. id: ${id}, fetchInitiatedForCurrentId: ${fetchInitiatedForCurrentId.current}, showPasswordModal: ${showPasswordModal}`);
    if (id && !fetchInitiatedForCurrentId.current && !showPasswordModal) {
      console.log('v.11 useEffect: Conditions met. Calling fetchContestDetails (initial).');
      fetchInitiatedForCurrentId.current = true;
      fetchContestDetails(undefined); // Initial call, no password attempt from form
    }

    const currentId = id;
    return () => {
      if (currentId !== id) {
        console.log('v.11 useEffect cleanup: ID changed. Resetting fetchInitiatedForCurrentId and other states.');
        fetchInitiatedForCurrentId.current = false;
        setContest(null);
        setShowPasswordModal(false);
        setPassword('');
        setPasswordError(null);
        setIsPasswordCorrect(false);
      } else {
        console.log('v.11 useEffect cleanup: Same ID (StrictMode unmount). fetchInitiatedForCurrentId remains:', fetchInitiatedForCurrentId.current);
      }
    };
  }, [id, showPasswordModal, user]);

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null); 
    if (password) { // `password` here is from the input field state
      fetchContestDetails(password); // User is attempting with a password from the form
    } else {
      setPasswordError('Password cannot be empty.');
    }
  };

  const handleSubmitText = () => {
    if (!isAuthenticated) {
      return;
    }
    
    setShowSubmitTextModal(true);
  };
  
  const handleSubmissionSuccess = () => {
    setShowSubmitTextModal(false);
    setSubmissionStatusMessage("Text submitted successfully!");
    fetchContestDetails(password);
    setTimeout(() => setSubmissionStatusMessage(null), 3000); // Clear message after 3 seconds
  };
  
  const handleJudge = () => {
    if (!isAuthenticated) {
      return;
    }
    
    setShowJudgeModal(true);
  };
  
  // Function to fetch available judge agents
  const fetchAvailableJudgeAgents = async () => {
    try {
      setIsLoadingJudgeAgents(true);
      // Get contest judges to filter only registered AI agents
      const contestJudges = await contestService.getContestJudges(parseInt(id || '1'));
      const agents = await getAgents();
      
      // Filter to only include agents that are registered as judges for this contest
      const registeredAgentIds = contestJudges
        .filter(judge => judge.agent_judge_id)
        .map(judge => judge.agent_judge_id);
      
      const judgeAgents = agents.filter(agent => 
        agent.type === 'judge' && registeredAgentIds.includes(agent.id)
      );
      
      setAvailableJudgeAgents(judgeAgents);
    } catch (err) {
      console.error('Error fetching judge agents:', err);
      toast.error('Failed to load AI judges. Please try again.');
      setAvailableJudgeAgents([]);
    } finally {
      setIsLoadingJudgeAgents(false);
    }
  };

  // Function to check judge completion status
  const checkJudgeCompletionStatus = async (contestId: number) => {
    if (!isAuthenticated || !user) {
      setJudgeCompletionStatus({ 
        totalJudges: 0,
        completedJudges: 0,
        userHasJudged: false,
        judgeDetails: [],
        isLoading: false
      });
      return;
    }

    try {
      setJudgeCompletionStatus(prev => ({ ...prev, isLoading: true }));
      
      // Get all judges for this contest
      const judges = await contestService.getContestJudges(contestId);
      
      // Check if current user has judged by checking their votes
      let userHasJudged = false;
      
      try {
        const userVotes = await getJudgeVotes(contestId, user.id);
        if (userVotes.length > 0) {
          userHasJudged = true;
        }
      } catch (err) {
        console.warn('Could not get user votes:', err);
        // Fallback: check if user is a human judge who has voted
        const userAsHumanJudge = judges.find(judge => judge.user_judge_id === user.id);
        if (userAsHumanJudge?.has_voted) {
          userHasJudged = true;
        }
      }
      
      const totalJudges = judges.length;
      const completedJudges = judges.filter(judge => judge.has_voted).length;
      
      const judgeDetails = judges.map(judge => ({
        name: judge.user_name || judge.agent_name || `Judge ${judge.id}`,
        type: judge.user_judge_id ? 'human' as const : 'ai' as const,
        completed: judge.has_voted || false
      }));
      
      setJudgeCompletionStatus({
        totalJudges,
        completedJudges,
        userHasJudged,
        judgeDetails,
        isLoading: false
      });
      
      console.log(`Judge completion status: ${completedJudges}/${totalJudges} judges completed, user has judged: ${userHasJudged}`);
    } catch (err: any) {
      console.error('Error checking judge completion status:', err);
      setJudgeCompletionStatus({ 
        totalJudges: 0,
        completedJudges: 0,
        userHasJudged: false,
        judgeDetails: [],
        isLoading: false
      });
    }
  };

  const handleAIJudge = () => {
    if (!isAuthenticated) {
      return;
    }
    
    setShowAIJudgeModal(true);
    // Fetch available judge agents when opening the modal
    fetchAvailableJudgeAgents();
  };
  
  const handleJudgingSuccess = (isAIJudge?: boolean) => {
    const wasAIJudge = isAIJudge ?? showAIJudgeModal;
    
    setShowJudgeModal(false);
    setShowAIJudgeModal(false);
    
    // Show success message with more specific information
    if (wasAIJudge) {
      toast.success('AI Judge evaluation completed successfully! Results have been added to the contest.');
    } else {
      toast.success('Your votes have been submitted successfully!');
    }
    
    // Refresh judge completion status to show updated counts
    if (contest?.id) {
      checkJudgeCompletionStatus(contest.id);
    }
  };

  // New function to handle text withdrawal
  const handleWithdrawText = async (textId: number) => {
    if (!contest || !id) return; // Ensure id is string for parseInt
    const textToWithdraw = userSubmissions.find(sub => sub.id === textId);
    if (!textToWithdraw) return;

    // Optional: Add a confirmation step here if desired
    if (!window.confirm(`Are you sure you want to withdraw "${textToWithdraw.title || 'this text'}"?`)) {
      return;
    }

    setIsProcessingWithdrawal(textId);
    try {
      // Call the API to withdraw the text
      await contestService.removeSubmissionFromContest(parseInt(id), textId); // Ensure id is parsed
      // After withdrawal, refresh only user submissions
      const refreshedSubmissions = await contestService.getContestMySubmissions(parseInt(id)); // Ensure id is parsed
      setUserSubmissions(refreshedSubmissions);
      // Also refresh all texts if they are currently displayed (e.g. if admin withdrew their own text during evaluation)
      if (texts.some(t => t.id === textId)) {
        fetchContestDetails(password); 
      }
      toast.success("Text withdrawn successfully");
    } catch (error) {
      console.error("Error withdrawing text:", error);
      toast.error("Failed to withdraw text. Please try again.");
    } finally {
      setIsProcessingWithdrawal(null);
    }
  };

  // Helper function to get preview of text content
  const getTextPreview = (content: string) => {
    const maxLength = 200;
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };
  
  // Function to open the full text modal
  const openFullTextModal = (text: contestService.ContestText) => {
    setSelectedTextForModal(text);
    setShowFullTextModal(true);
  };
  
  // Function to close the full text modal
  const closeFullTextModal = () => {
    setSelectedTextForModal(null);
    setShowFullTextModal(false);
  };

  // New function for admin/creator to withdraw any text
  const handleAdminWithdrawText = async (textId: number) => {
    if (!contest || !id || (!user?.is_admin && user?.id !== contest.creator.id)) return;

    const textToWithdraw = texts.find(sub => sub.id === textId);
    if (!textToWithdraw) return;

    if (!window.confirm(`ADMIN ACTION: Are you sure you want to withdraw "${textToWithdraw.title || 'this text'} by user ${textToWithdraw.author?.username || 'Unknown'}?`)) {
      return;
    }

    setIsProcessingAdminWithdrawal(textId);
    try {
      await contestService.removeSubmissionFromContest(parseInt(id), textId);
      toast.success("Text withdrawn successfully by admin/creator.");
      // Refresh contest details to update the list of all texts
      fetchContestDetails(password); 
    } catch (error) {
      console.error("Error withdrawing text by admin/creator:", error);
      toast.error("Failed to withdraw text. Please try again.");
    } finally {
      setIsProcessingAdminWithdrawal(null);
    }
  };

  // Update the handleVolunteerAsJudge function to use user_judge_id
  const handleVolunteerAsJudge = async () => {
    if (!isAuthenticated || !user || !contest) {
      return;
    }
    
    try {
      setIsFetching(true);
      // Call the API to add the current user as a judge with the correct field name
      await contestService.assignJudgeToContest(contest.id, { user_id: user.id });
      toast.success('You have been added as a judge for this contest.');
      
      // Update the judge status to reflect the change
      setIsJudge(true);
    } catch (err: any) {
      console.error('Error volunteering as judge:', err);
      
      // Check if it's a 409 conflict error (already a judge)
      if (err.response && err.response.status === 409) {
        toast.success('You are already a judge for this contest.');
        setIsJudge(true); // Update UI since they are actually a judge
      } else {
        toast.error('Failed to register as a judge. Please try again.');
      }
    } finally {
      setIsFetching(false);
    }
  };

  if (isLoading) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500">Loading contest details...</p>
      </div>
    );
  }
  
  if (showPasswordModal) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
          <h2 className="text-xl font-bold mb-4">Private Contest</h2>
          <p className="mb-4 text-gray-600">This contest is password-protected. Please enter the password to view details.</p>
          
          <form onSubmit={handlePasswordSubmit}>
            <div className="mb-4">
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                id="password"
                className="w-full px-3 py-2 border rounded-lg"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              {passwordError && (
                <p className="mt-1 text-sm text-red-600">{passwordError}</p>
              )}
            </div>
            
            <div className="flex justify-end">
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Submit
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }
  
  if (!contest) {
    return (
      <div className="text-center py-16 bg-gray-50 rounded-lg">
        <h2 className="text-xl font-bold text-gray-700 mb-2">Contest Not Found</h2>
        <p className="text-gray-500 mb-4">The contest you're looking for doesn't exist or has been removed. Or, it might be a private contest pending password entry.</p>
        <Link to="/contests" className="text-indigo-600 hover:text-indigo-800">
          Back to Contest List
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <div className="flex justify-between items-start mb-2">
          <h1 className="text-3xl font-bold">{contest.title}</h1>
          <div className="flex items-center space-x-2">
            {(user?.is_admin || user?.id === contest?.creator.id) && (
              <Link 
                to={`/dashboard`}
                onClick={() => {
                  // Optional: If dashboard can highlight/scroll to the contest tab or specific contest, add logic here or via state/URL params.
                  // For now, just navigates to the main dashboard.
                  // Consider using navigate hook if more complex state passing is needed upon navigation.
                }}
                className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
              >
                Manage Contest in Dashboard
              </Link>
            )}
            <div 
              className={`text-xs px-2 py-1 rounded-full ${
                contest.type === 'public' 
                  ? 'bg-blue-100 text-blue-800' 
                  : 'bg-purple-100 text-purple-800'
              }`}
            >
              {contest.type.charAt(0).toUpperCase() + contest.type.slice(1)}
            </div>
            <div 
              className={`text-xs px-2 py-1 rounded-full ${
                contest.status === 'open' 
                  ? 'bg-green-100 text-green-800' 
                  : contest.status === 'evaluation' 
                    ? 'bg-yellow-100 text-yellow-800' 
                    : 'bg-gray-100 text-gray-800'
              }`}
            >
              {contest.status.charAt(0).toUpperCase() + contest.status.slice(1)}
            </div>
          </div>
        </div>
        
        <p className="text-gray-600 mb-4">{contest.description}</p>
        
        <div className="flex flex-wrap gap-4 text-sm text-gray-500 mb-6">
          <div>
            <span className="font-medium">Created by:</span> {contest.creator.username}
          </div>
          <div>
            <span className="font-medium">Created:</span> {new Date(contest.created_at).toLocaleDateString()}
          </div>
          <div>
            <span className="font-medium">Last updated:</span> {new Date(contest.last_modified).toLocaleDateString()}
          </div>
          {contest.end_date && (
            <div>
              <span className="font-medium">End date:</span> {new Date(contest.end_date).toLocaleDateString()}
            </div>
          )}
          <div>
            <span className="font-medium">Participants:</span> {contest.participant_count}
          </div>
          <div>
            <span className="font-medium">Submissions:</span> {contest.text_count}
          </div>
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-sm mb-8">
        <h2 className="text-xl font-bold mb-4">Contest Details</h2>
        <div className="prose max-w-none">
          <pre className="whitespace-pre-wrap">{contest.full_description || contest.description}</pre>
        </div>
      </div>
      
      {contest.status === 'open' && (
        <div className="bg-white p-6 rounded-lg shadow-sm mb-8">
          <h2 className="text-xl font-bold mb-4">Submit Your Entry</h2>
          
          {/* Submission Success Message */} 
          {submissionStatusMessage && (
            <div className="mb-4 p-3 bg-green-100 text-green-700 border border-green-200 rounded-md">
              {submissionStatusMessage}
            </div>
          )}

          {isAuthenticated && contest ? (
            <div>
              {/* List User's Current Submissions */} 
              {userSubmissions.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-700 mb-3">Your Submitted Texts:</h3>
                  <ul className="space-y-3">
                    {userSubmissions.map(sub => (
                      <li key={sub.id} className="flex justify-between items-center p-3 bg-gray-50 border border-gray-200 rounded-md">
                        <span className="text-gray-800">{sub.title || 'Untitled Submission'}</span>
                        <button
                          onClick={() => handleWithdrawText(sub.id)}
                          className="text-sm font-medium text-red-600 hover:text-red-800 disabled:opacity-50 transition-opacity duration-150"
                          disabled={isProcessingWithdrawal === sub.id}
                        >
                          {isProcessingWithdrawal === sub.id ? 'Withdrawing...' : 'Withdraw'}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Submit New Text Button/Message */} 
              {(() => {
                if (contest.author_restrictions && userSubmissions.length > 0) {
                  // Single submission allowed, and user has already submitted.
                  return <p className="text-gray-600">You have already submitted your entry for this contest. To submit a different text, please withdraw your current submission first.</p>;
                } else {
                  // Either multiple submissions allowed, or single submission allowed and user hasn't submitted yet.
                  return (
                    <div>
                      <p className="mb-4 text-gray-600">
                        {contest.author_restrictions 
                          ? "Ready to participate? Submit your text to this contest."
                          : (userSubmissions.length > 0 
                              ? "This contest allows multiple submissions. Feel free to submit another text."
                              : "Ready to participate? This contest allows multiple submissions."
                            )
                      }
                      </p>
                      <button 
                        onClick={handleSubmitText}
                        className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                      >
                        Submit Text
                      </button>
                    </div>
                  );
                }
              })()}
            </div>
          ) : (
            <div>
              <p className="mb-4">You need to be logged in to submit a text to this contest.</p>
              <Link 
                to="/login"
                className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Login to Submit
              </Link>
            </div>
          )}
        </div>
      )}
      
      {contest.status === 'evaluation' && (
        <div className="bg-white p-6 rounded-lg shadow-sm mb-8">
          <h2 className="text-xl font-bold mb-4">Submissions Under Evaluation</h2>
          
          {texts.length === 0 ? (
            <p className="text-gray-500">No texts have been submitted to this contest.</p>
          ) : (
            <div>
              <div className="mb-6">
                <p className="text-gray-600 mb-4">
                  This contest is currently being evaluated by judges. Results will be available once the evaluation phase is complete.
                </p>
                
                {/* User Voting Status Indicator */}
                {isAuthenticated && user && (
                  <div className="mb-4">
                    {judgeCompletionStatus.isLoading ? (
                      <div className="p-3 bg-blue-50 text-blue-700 rounded-md">
                        <p className="text-sm">Checking your voting status...</p>
                      </div>
                    ) : judgeCompletionStatus.userHasJudged ? (
                      <div className="p-3 bg-green-50 text-green-700 rounded-md border border-green-200">
                        <p className="font-medium">✓ You have completed your evaluation</p>
                        <p className="text-sm">
                          You can vote again to update your choices.
                        </p>
                      </div>
                    ) : isJudge ? (
                      <div className="p-3 bg-yellow-50 text-yellow-700 rounded-md border border-yellow-200">
                        <p className="font-medium">⏳ You haven't evaluated yet</p>
                        <p className="text-sm">As a judge, your evaluation is needed to help determine the contest results.</p>
                      </div>
                    ) : null}
                  </div>
                )}
                
                {/* Judge completion overview */}
                {judgeCompletionStatus.totalJudges > 0 && (
                  <div className="mt-3 p-3 bg-blue-50 text-blue-700 rounded-md border border-blue-200">
                    <p className="font-medium">
                      Judge Progress: {judgeCompletionStatus.completedJudges}/{judgeCompletionStatus.totalJudges} completed
                    </p>
                    <div className="mt-2 text-sm">
                      {judgeCompletionStatus.judgeDetails.map((judge, index) => (
                        <div key={index} className="flex items-center space-x-2">
                          <span className={judge.completed ? 'text-green-600' : 'text-gray-500'}>
                            {judge.completed ? '✓' : '○'}
                          </span>
                          <span>
                            {judge.name} ({judge.type === 'human' ? 'Human' : 'AI'})
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {isJudge || (isAuthenticated && user?.id === contest?.creator.id) ? (
                  <div className="mt-6 flex flex-col sm:flex-row sm:space-x-4 space-y-3 sm:space-y-0">
                    <button
                      onClick={handleJudge}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                    >
                      Judge Submissions
                    </button>
                    <button
                      onClick={handleAIJudge}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Use AI Judge
                    </button>
                  </div>
                ) : isAuthenticated ? (
                  <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md text-yellow-700">
                    {!contest.judge_restrictions ? (
                      <div>
                        <p className="mb-3">This contest allows volunteers to judge the submissions.</p>
                        <button
                          onClick={handleVolunteerAsJudge}
                          disabled={isFetching}
                          className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50"
                        >
                          {isFetching ? 'Processing...' : 'Volunteer as Judge'}
                        </button>
                      </div>
                    ) : (
                      <p>You are not assigned as a judge for this contest. Only assigned judges can submit evaluations.</p>
                    )}
                  </div>
                ) : (
                  <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-md text-gray-700">
                    <p>You need to be logged in and assigned as a judge to evaluate submissions.</p>
                    <Link
                      to="/login"
                      className="inline-block mt-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                    >
                      Login to Continue
                    </Link>
                  </div>
                )}
              </div>
              
              <div className="space-y-6">
                {texts.map((text) => (
                  <div key={text.id} className="border-b pb-6 last:border-b-0">
                    <div className="flex justify-between items-start">
                      <h3 className="text-lg font-semibold mb-2">{text.title}</h3>
                      {(user?.is_admin || user?.id === contest?.creator.id) && contest.status === 'evaluation' && (
                        <button
                          onClick={() => handleAdminWithdrawText(text.id)}
                          className="ml-4 text-sm font-medium text-red-600 hover:text-red-800 disabled:opacity-50 transition-opacity duration-150"
                          disabled={isProcessingAdminWithdrawal === text.id}
                        >
                          {isProcessingAdminWithdrawal === text.id ? 'Withdrawing...' : 'Withdraw (Admin)'}
                        </button>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mb-1">Submitted by: {text.author?.username || 'Anonymous'}</p>
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded">
                        {getTextPreview(text.content)}
                      </pre>
                      <button
                        type="button"
                        onClick={() => openFullTextModal(text)}
                        className="mt-2 text-sm text-indigo-600 hover:text-indigo-800"
                      >
                        Show Full Content
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {contest.status === 'closed' && (
        <div className="bg-white p-6 rounded-lg shadow-sm mb-8">
          <h2 className="text-xl font-bold mb-4">Contest Results</h2>
          
          {texts.length === 0 ? (
            <p className="text-gray-500">No texts were submitted to this contest.</p>
          ) : (
            <ContestResults 
              contestId={parseInt(id || '1')} 
              texts={texts.map(text => ({
                id: text.text_id,
                title: text.title,
                content: text.content,
                owner_id: text.owner_id || 0,
                author: text.author?.username || (typeof text.author === 'string' ? text.author as string : 'Unknown'),
                created_at: text.created_at || text.submission_date || '',
                updated_at: text.updated_at || text.submission_date || '',
                ranking: text.ranking,
                total_points: text.total_points,
                evaluations: text.evaluations,
              }))} 
            />
          )}
        </div>
      )}
      
      {showSubmitTextModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="max-w-2xl w-full mx-4">
            <TextSubmissionForm
              contestId={parseInt(id || '1')}
              isPrivate={contest?.type === 'private'}
              password={password}
              onSuccess={handleSubmissionSuccess}
              onCancel={() => setShowSubmitTextModal(false)}
            />
          </div>
        </div>
      )}
      
      {showJudgeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="max-w-4xl w-full mx-4 max-h-screen overflow-y-auto p-4">
            <HumanJudgingForm
              contestId={parseInt(id || '1')}
              texts={texts.map(text => ({
                id: text.text_id,
                title: text.title,
                content: text.content,
                owner_id: text.owner_id || 0,
                author: text.author?.username || (typeof text.author === 'string' ? text.author as string : 'Unknown'),
                created_at: text.created_at || text.submission_date || '',
                updated_at: text.updated_at || text.submission_date || '',
              }))}
              onSuccess={() => handleJudgingSuccess(false)}
              onCancel={() => setShowJudgeModal(false)}
            />
          </div>
        </div>
      )}
      
      {showAIJudgeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="max-w-2xl w-full mx-4">
            <AIJudgeExecutionForm
              contestId={parseInt(id || '1')}
              contestTextCount={texts.length}
              averageTextLength={averageTextLength}
              onSuccess={() => handleJudgingSuccess(true)}
              onCancel={() => setShowAIJudgeModal(false)}
              availableAgents={availableJudgeAgents}
            />
          </div>
        </div>
      )}
      
      {/* Full Text Modal */}
      {showFullTextModal && selectedTextForModal && (
        <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full h-[80vh] flex flex-col">
            {/* Modal header */}
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <h3 className="text-xl font-bold">
                {selectedTextForModal.title || 'Text Content'}
              </h3>
              <button 
                onClick={closeFullTextModal}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Modal content */}
            <div className="px-6 py-4 overflow-y-auto flex-grow">
              <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded text-base">
                {selectedTextForModal.content}
              </pre>
            </div>
            
            {/* Modal footer */}
            <div className="px-6 py-4 border-t">
              <button
                onClick={closeFullTextModal}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContestDetailPage; 