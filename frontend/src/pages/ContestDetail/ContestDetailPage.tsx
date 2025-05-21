import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import * as contestService from '../../services/contestService';
import TextSubmissionForm from '../../components/Contest/TextSubmissionForm';
import HumanJudgingForm from '../../components/Contest/HumanJudgingForm';
import AIJudgeExecutionForm from '../../components/Contest/AIJudgeExecutionForm';
import ContestResults from '../../components/Contest/ContestResults';
import { toast } from 'react-hot-toast';
import MarkdownEditor from '../../components/MarkdownEditor';
import TextSelectionModal from '../../components/TextSelectionModal';
import JudgingForm from '../../components/Contest/JudgingForm';

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

    // New states for managing user's specific submissions and withdrawal process
    const [userSubmissions, setUserSubmissions] = useState<contestService.ContestText[]>([]);
    const [isProcessingWithdrawal, setIsProcessingWithdrawal] = useState<number | null>(null);

    // New state for admin/creator withdrawal processing
    const [isProcessingAdminWithdrawal, setIsProcessingAdminWithdrawal] = useState<number | null>(null);

    // New state for submission success message
    const [submissionStatusMessage, setSubmissionStatusMessage] = useState<string | null>(null);

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

      // Determine if user has access to the contest
      const isCreator = user?.id === contestDataForPage.creator.id;
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
          const canViewAllSubmissions =
              (contestDataForPage.status === 'evaluation' || contestDataForPage.status === 'closed') ||
              ((contestDataForPage.status === 'open' || contestDataForPage.status === 'evaluation') && isCreator);

          if (canViewAllSubmissions) {
            try {
              const allSubmissionsData = await contestService.getContestSubmissions(parseInt(id), actualPasswordToUseForSubCalls);
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
            setIsJudge(judges.some(judge => judge.user_id === user.id));
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
  
  const handleAIJudge = () => {
    if (!isAuthenticated) {
      return;
    }
    
    setShowAIJudgeModal(true);
  };
  
  const handleJudgingSuccess = () => {
    setShowJudgeModal(false);
    setShowAIJudgeModal(false);
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
          <div className="flex space-x-2">
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
                
                {isJudge && (
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
                      <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded">{text.content}</pre>
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
                id: text.id,
                title: text.title,
                content: text.content,
                owner_id: text.owner_id || 0,
                author: text.author?.username || (typeof text.author === 'string' ? text.author as string : 'Unknown'),
                created_at: text.created_at || text.submission_date || '',
                updated_at: text.updated_at || text.submission_date || '',
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
                id: text.id,
                title: text.title,
                content: text.content,
                owner_id: text.owner_id || 0,
                author: text.author?.username || (typeof text.author === 'string' ? text.author as string : 'Unknown'),
                created_at: text.created_at || text.submission_date || '',
                updated_at: text.updated_at || text.submission_date || '',
              }))}
              onSuccess={handleJudgingSuccess}
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
              onSuccess={handleJudgingSuccess}
              onCancel={() => setShowAIJudgeModal(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ContestDetailPage; 