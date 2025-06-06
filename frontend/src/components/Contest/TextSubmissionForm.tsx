import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Text } from '../../services/textService';
import { getUserTexts } from '../../services/textService';
import { submitTextToContest, getContestMySubmissions } from '../../services/contestService';

interface TextSubmissionFormProps {
  contestId: number;
  passwordProtected: boolean;
  password?: string;
  onSuccess: () => void;
  onCancel: () => void;
  judgeRestrictions?: boolean;
  isUserJudge?: boolean;
  endDate?: string | null;
}

const TextSubmissionForm: React.FC<TextSubmissionFormProps> = ({
  contestId,
  passwordProtected,
  password,
  onSuccess,
  onCancel,
  judgeRestrictions = false,
  isUserJudge = false,
  endDate
}) => {
  const navigate = useNavigate();
  const [texts, setTexts] = useState<Text[]>([]);
  const [selectedTextId, setSelectedTextId] = useState<number | ''>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submittedTextIds, setSubmittedTextIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    const fetchTexts = async () => {
      try {
        setIsLoading(true);
        
        // Fetch user's texts
        const userTexts = await getUserTexts();
        setTexts(userTexts);
        
        // Fetch user's submissions for this contest
        try {
          const mySubmissions = await getContestMySubmissions(contestId);
          const submittedIds = new Set(mySubmissions.map(submission => submission.text_id));
          setSubmittedTextIds(submittedIds);
        } catch (submissionErr) {
          console.warn('Could not fetch user submissions:', submissionErr);
          // Don't set error for this, as it might be expected if no submissions exist
        }
        
        setIsLoading(false);
      } catch (err) {
        console.error('Error fetching texts:', err);
        setError('Failed to load your texts. Please try again.');
        setIsLoading(false);
      }
    };

    fetchTexts();
  }, [contestId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedTextId) {
      setError('Please select a text to submit.');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      await submitTextToContest(
        contestId, 
        Number(selectedTextId),
        passwordProtected ? password : undefined
      );
      
      setIsLoading(false);
      onSuccess();
    } catch (err: any) {
      console.error('Error submitting text:', err);
      setError(err.response?.data?.message || 'Failed to submit text. Please try again.');
      setIsLoading(false);
    }
  };

  const handleCreateNewText = () => {
    navigate('/dashboard?tab=texts&action=create&contestId=' + contestId);
  };

  // Check if contest deadline has passed
  const isDeadlineExpired = () => {
    if (!endDate) return false;
    const now = new Date();
    const deadline = new Date(endDate);
    return now > deadline;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 max-w-lg mx-auto">
      <h2 className="text-xl font-bold mb-4">Submit Text to Contest</h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
          {error}
        </div>
      )}

      {/* Deadline warning */}
      {endDate && (() => {
        const now = new Date();
        const deadline = new Date(endDate);
        const isExpired = now > deadline;
        
        if (isExpired) {
          return (
            <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
              <div className="flex items-center">
                <span className="mr-2">⏰</span>
                <span>This contest's deadline has passed ({deadline.toLocaleDateString()}). Submissions are no longer accepted.</span>
              </div>
            </div>
          );
        }
        
        // Show warning if deadline is within 24 hours
        const timeLeft = deadline.getTime() - now.getTime();
        const hoursLeft = Math.floor(timeLeft / (1000 * 60 * 60));
        
        if (hoursLeft <= 24 && hoursLeft > 0) {
          return (
            <div className="mb-4 p-3 bg-yellow-50 text-yellow-700 rounded-md">
              <div className="flex items-center">
                <span className="mr-2">⚠️</span>
                <span>Deadline approaching: {hoursLeft} hours remaining (until {deadline.toLocaleDateString()})</span>
              </div>
            </div>
          );
        }
        
        return null;
      })()}

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="text-select" className="block text-sm font-medium text-gray-700 mb-1">
            Select Text
          </label>
          
          {isLoading ? (
            <p className="text-gray-500">Loading your texts...</p>
          ) : texts.length === 0 ? (
            <p className="text-gray-500 mb-2">You don't have any texts yet. Create one first.</p>
          ) : (
            <>
              <select
                id="text-select"
                className="w-full p-2 border rounded-md"
                value={selectedTextId}
                onChange={(e) => setSelectedTextId(Number(e.target.value))}
              >
                <option value="">-- Select a text --</option>
                {texts.map((text) => {
                  const isSubmitted = submittedTextIds.has(text.id);
                  return (
                    <option 
                      key={text.id} 
                      value={text.id}
                      disabled={isSubmitted}
                    >
                      {text.title}{isSubmitted ? ' (Already submitted to this contest)' : ''}
                    </option>
                  );
                })}
              </select>
              {submittedTextIds.size > 0 && (
                <p className="mt-2 text-sm text-gray-600">
                  <span className="font-medium">Note:</span> Texts marked as "Already submitted" cannot be submitted again unless withdrawn first.
                </p>
              )}
            </>
          )}
        </div>
        
        <div className="flex items-center justify-between mt-6">
          <button
            type="button"
            className="py-2 px-4 bg-indigo-100 text-indigo-700 rounded-md hover:bg-indigo-200"
            onClick={handleCreateNewText}
          >
            Create New Text
          </button>
          
          <div className="flex space-x-3">
            <button
              type="button"
              className="py-2 px-4 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
              onClick={onCancel}
            >
              Cancel
            </button>
            
            <button
              type="submit"
              className={`py-2 px-4 rounded-md ${
                judgeRestrictions && isUserJudge
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : isDeadlineExpired()
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-indigo-300'
              }`}
              disabled={!selectedTextId || isLoading || (judgeRestrictions && isUserJudge) || isDeadlineExpired()}
              title={
                judgeRestrictions && isUserJudge 
                  ? 'Judges cannot submit texts to this contest due to judge restrictions'
                  : isDeadlineExpired()
                    ? 'Contest deadline has passed. Submissions are no longer accepted.'
                    : ''
              }
            >
              {isLoading ? 'Submitting...' : 'Submit Text'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default TextSubmissionForm; 