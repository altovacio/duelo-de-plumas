import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { getContest, getContestSubmissions, getContestJudges, Contest as ContestServiceType } from '../../services/contestService';
import TextSubmissionForm from '../../components/Contest/TextSubmissionForm';
import HumanJudgingForm from '../../components/Contest/HumanJudgingForm';
import AIJudgeExecutionForm from '../../components/Contest/AIJudgeExecutionForm';
import ContestResults from '../../components/Contest/ContestResults';
import { Text as TextType } from '../../services/textService';

// Use the Contest type from the service, potentially extended if needed locally
// For now, assume ContestServiceType is sufficient, but we need to handle 'creator' if it's different.
// The service defines `creator_id`, but this page expects a `creator` object.
// This implies the actual response for getContest might be richer than the generic ContestServiceType.
// We'll define a local type that reflects what this page *expects* getContest to return,
// aligning fields with ContestServiceType where possible.

interface ContestPageSpecificData extends Omit<ContestServiceType, 'creator_id' | 'updated_at' | 'is_private' | 'has_password' | 'min_votes_required'> {
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
    const [texts, setTexts] = useState<ContestText[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [password, setPassword] = useState<string>('');
    const [isPasswordCorrect, setIsPasswordCorrect] = useState<boolean>(false);
    const [passwordError, setPasswordError] = useState<string | null>(null);
    const [showPasswordModal, setShowPasswordModal] = useState<boolean>(false);
    
    // States for modal dialogs
    const [showSubmitTextModal, setShowSubmitTextModal] = useState<boolean>(false);
    const [showJudgeModal, setShowJudgeModal] = useState<boolean>(false);
    const [showAIJudgeModal, setShowAIJudgeModal] = useState<boolean>(false);
    const [isJudge, setIsJudge] = useState<boolean>(false);
    const [hasSubmitted, setHasSubmitted] = useState<boolean>(false);
    const [averageTextLength, setAverageTextLength] = useState<number>(1000); // Default estimate

  useEffect(() => {
    const fetchContestDetails = async () => {
      try {
        setIsLoading(true);
        
        // Fetch contest details
        const contestDataFromService = await getContest(parseInt(id || '1'), isPasswordCorrect ? password : undefined);
        
        // Transform data from ContestServiceType to ContestPageSpecificData
        const contestDataForPage: ContestPageSpecificData = {
          ...contestDataFromService,
          // Assuming backend for this specific endpoint sends a creator object
          // If it sends creator_id, this will need adjustment or a separate fetch for user details
          creator: contestDataFromService.creator_id ? { id: contestDataFromService.creator_id, username: 'Fetching...' } : { id: 0, username: 'Unknown' }, // Placeholder, ideally backend sends this or needs another fetch
          full_description: contestDataFromService.description, // Assuming full_description is part of description or needs specific handling
          last_modified: contestDataFromService.updated_at,
          type: contestDataFromService.is_private ? 'private' : 'public',
          is_password_protected: contestDataFromService.has_password,
          min_required_votes: contestDataFromService.min_votes_required,
          // Explicitly map fields that are present in both but might be overlooked by spread if optional
          participant_count: contestDataFromService.participant_count || 0,
          text_count: contestDataFromService.text_count || 0,
        };
        
        // If backend *actually* sends creator object for this endpoint:
        // const contestDataForPage = {
        //   ...contestDataFromService,
        //   // creator: contestDataFromService.creator, // if API sends it directly
        //   last_modified: contestDataFromService.updated_at,
        //   type: contestDataFromService.is_private ? 'private' : 'public',
        //   is_password_protected: contestDataFromService.has_password,
        //   min_required_votes: contestDataFromService.min_votes_required,
        // };


        setContest(contestDataForPage);
        
        // If contest is private and we haven't verified the password, show password modal
        if (contestDataForPage.type === 'private' && !isPasswordCorrect) {
          setShowPasswordModal(true);
          setIsLoading(false);
          return;
        }
        
        // Fetch submissions if appropriate
        if (
          contestDataForPage.status === 'evaluation' || 
          contestDataForPage.status === 'closed' ||
          // Also fetch if open but user is the creator to see current submissions
          (contestDataForPage.status === 'open' && contestDataForPage.creator.id === user?.id)
        ) {
          const submissionsData = await getContestSubmissions(
            parseInt(id || '1'),
            isPasswordCorrect ? password : undefined
          );
          
          // Convert API submission data to ContestText format
          const formattedTexts: ContestText[] = submissionsData.map(submission => ({
            id: submission.id,
            title: submission.title,
            content: submission.content,
            author: submission.author ? {
              id: submission.author.id,
              username: submission.author.username
            } : undefined,
            owner: submission.owner ? {
              id: submission.owner.id,
              username: submission.owner.username
            } : undefined,
            created_at: submission.created_at,
            updated_at: submission.updated_at || submission.created_at, // Populate updated_at
            // Votes would be populated from a separate API call in a real implementation
          }));
          
          setTexts(formattedTexts);
          
          // Calculate average text length for AI cost estimation
          if (formattedTexts.length > 0) {
            const totalLength = formattedTexts.reduce(
              (sum, text) => sum + text.content.length, 0
            );
            setAverageTextLength(Math.ceil(totalLength / formattedTexts.length));
          }
        }
        
        // Check if user is a judge for this contest
        if (isAuthenticated && user) {
          const judges = await getContestJudges(parseInt(id || '1'));
          setIsJudge(judges.some(judge => judge.user_id === user.id));
        }
        
        // Check if user has already submitted to this contest
        if (isAuthenticated && user && contestDataForPage.status === 'open') {
          // This is a simplification - in reality, you'd check if the user has submissions
          setHasSubmitted(false); // Default assumption
        }
        
        setIsLoading(false);
      } catch (err) {
        console.error('Error fetching contest details:', err);
        setIsLoading(false);
      }
    };
    
    if (id) {
      fetchContestDetails();
    }
  }, [id, isPasswordCorrect, password, isAuthenticated, user]);

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // This would make an API call to verify the password
    if (password === 'password123') { // Mock correct password
      setIsPasswordCorrect(true);
      setShowPasswordModal(false);
      setPasswordError(null);
    } else {
      setPasswordError('Incorrect password. Please try again.');
    }
  };

  // Handle text submission
  const handleSubmitText = () => {
    if (!isAuthenticated) {
      // Redirect to login
      return;
    }
    
    setShowSubmitTextModal(true);
  };
  
  // Handle submission success
  const handleSubmissionSuccess = () => {
    setShowSubmitTextModal(false);
    setHasSubmitted(true);
    // Refresh contest data
    // This would be replaced with an actual API call in a real implementation
  };
  
  // Handle judge actions
  const handleJudge = () => {
    if (!isAuthenticated) {
      // Redirect to login
      return;
    }
    
    setShowJudgeModal(true);
  };
  
  // Handle AI judge execution
  const handleAIJudge = () => {
    if (!isAuthenticated) {
      // Redirect to login
      return;
    }
    
    setShowAIJudgeModal(true);
  };
  
  // Handle judging success
  const handleJudgingSuccess = () => {
    setShowJudgeModal(false);
    setShowAIJudgeModal(false);
    // Refresh contest data
    // This would be replaced with an actual API call in a real implementation
  };

  if (isLoading) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500">Loading contest details...</p>
      </div>
    );
  }
  
  if (!contest) {
    return (
      <div className="text-center py-16 bg-gray-50 rounded-lg">
        <h2 className="text-xl font-bold text-gray-700 mb-2">Contest Not Found</h2>
        <p className="text-gray-500 mb-4">The contest you're looking for doesn't exist or has been removed.</p>
        <Link to="/contests" className="text-indigo-600 hover:text-indigo-800">
          Back to Contest List
        </Link>
      </div>
    );
  }
  
  // Password protection modal
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

  return (
    <div>
      {/* Contest Header */}
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
      
      {/* Contest Full Description */}
      <div className="bg-white p-6 rounded-lg shadow-sm mb-8">
        <h2 className="text-xl font-bold mb-4">Contest Details</h2>
        <div className="prose max-w-none">
          {/* This would use react-markdown to render Markdown content */}
          <pre className="whitespace-pre-wrap">{contest.full_description || contest.description}</pre>
        </div>
      </div>
      
      {/* Contest State-specific Content */}
      {contest.status === 'open' && (
        <div className="bg-white p-6 rounded-lg shadow-sm mb-8">
          <h2 className="text-xl font-bold mb-4">Submit Your Entry</h2>
          
          {isAuthenticated ? (
            hasSubmitted ? (
              <div>
                <p className="mb-4">You have already submitted a text to this contest.</p>
                <button
                  onClick={() => setHasSubmitted(false)} // In a real app, this would withdraw the submission
                  className="text-red-600 hover:text-red-800 font-medium"
                >
                  Withdraw Submission
                </button>
              </div>
            ) : (
              <div>
                <p className="mb-4">Ready to participate? Submit your text to this contest.</p>
                <button 
                  onClick={handleSubmitText}
                  className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  Submit Text
                </button>
              </div>
            )
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
                {/* Display anonymized texts for evaluation phase */}
                {texts.map((text) => (
                  <div key={text.id} className="border-b pb-6 last:border-b-0">
                    <h3 className="text-lg font-semibold mb-2">{text.title}</h3>
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
              texts={texts.map(text => ({ // Map ContestText to TextType
                id: text.id,
                title: text.title,
                content: text.content,
                owner_id: text.owner?.id || text.author?.id || 0, // Determine owner_id. Ensure it's always a number.
                author: text.author?.username || (typeof text.author === 'string' ? text.author : 'Unknown'), // Handle if author is string or object
                created_at: text.created_at,
                updated_at: text.updated_at || text.created_at, // Ensure updated_at is present
              }))} 
            />
          )}
        </div>
      )}
      
      {/* Text Submission Modal */}
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
      
      {/* Human Judging Modal */}
      {showJudgeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="max-w-4xl w-full mx-4 max-h-screen overflow-y-auto p-4">
            <HumanJudgingForm
              contestId={parseInt(id || '1')}
              texts={texts.map(text => ({ // Map ContestText to TextType
                id: text.id,
                title: text.title,
                content: text.content,
                owner_id: text.owner?.id || text.author?.id || 0, // Determine owner_id. Ensure it's always a number.
                author: text.author?.username || (typeof text.author === 'string' ? text.author : 'Unknown'), // Handle if author is string or object
                created_at: text.created_at,
                updated_at: text.updated_at || text.created_at, // Ensure updated_at is present
              }))}
              onSuccess={handleJudgingSuccess}
              onCancel={() => setShowJudgeModal(false)}
            />
          </div>
        </div>
      )}
      
      {/* AI Judge Modal */}
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