import React, { useState, useEffect } from 'react';
import { Text } from '../../services/textService';
import { submitVote, CreateVoteRequest, getJudgeVotes, Vote } from '../../services/voteService';
import { useAuth } from '../../hooks/useAuth';

interface HumanJudgingFormProps {
  contestId: number;
  texts: Text[];
  onSuccess: () => void;
  onCancel: () => void;
}

const HumanJudgingForm: React.FC<HumanJudgingFormProps> = ({
  contestId,
  texts,
  onSuccess,
  onCancel
}) => {
  console.log('[HumanJudgingForm] Component loaded with new features v2.0');
  const { user } = useAuth();
  // State for storing place (ranking) selections
  const [firstPlace, setFirstPlace] = useState<number | null>(null);
  const [secondPlace, setSecondPlace] = useState<number | null>(null);
  const [thirdPlace, setThirdPlace] = useState<number | null>(null);
  
  // State for storing comments
  const [comments, setComments] = useState<Record<number, string>>({});
  
  // State for tracking currently displayed full text (modal)
  const [fullTextModalId, setFullTextModalId] = useState<number | null>(null);
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // State for existing votes
  const [existingVotes, setExistingVotes] = useState<Vote[]>([]);
  const [isLoadingExistingVotes, setIsLoadingExistingVotes] = useState(true);
  
  // Calculate minimum required votes based on texts count
  const minRequiredVotes = Math.min(3, texts.length);
  
  // Load existing votes when component mounts
  useEffect(() => {
    const loadExistingVotes = async () => {
      if (!user) return;
      
      try {
        setIsLoadingExistingVotes(true);
        console.log(`Loading existing votes for user ${user.id} in contest ${contestId}`);
        const votes = await getJudgeVotes(contestId, user.id);
        console.log('Loaded existing votes:', votes);
        setExistingVotes(votes);
        
        // Pre-populate the form with existing votes
        votes.forEach(vote => {
          if (vote.place === 1) setFirstPlace(vote.text_id);
          if (vote.place === 2) setSecondPlace(vote.text_id);
          if (vote.place === 3) setThirdPlace(vote.text_id);
          if (vote.comment) {
            setComments(prev => ({ ...prev, [vote.text_id]: vote.comment }));
          }
        });
      } catch (err: any) {
        console.error('Error loading existing votes:', err);
        // If it's a 403 error, the user might not be registered as a judge yet
        if (err.response?.status === 403) {
          console.log('User not yet registered as judge, continuing without existing votes');
        } else if (err.response?.status === 404) {
          console.log('No existing votes found for this user in this contest');
        } else {
          console.warn('Unexpected error loading existing votes:', err.message);
        }
        // Don't show error for this, as it might be expected if no votes exist yet or user isn't judge
        setExistingVotes([]);
      } finally {
        setIsLoadingExistingVotes(false);
      }
    };
    
    loadExistingVotes();
  }, [contestId, user]);
  
  // Get existing vote for a text
  const getExistingVote = (textId: number): Vote | undefined => {
    return existingVotes.find(vote => vote.text_id === textId);
  };
  
  // Handle place selection
  const handlePlaceSelection = (place: 1 | 2 | 3, textId: number) => {
    // If this text is already selected for another place, unselect it there
    if (textId === firstPlace && place !== 1) setFirstPlace(null);
    if (textId === secondPlace && place !== 2) setSecondPlace(null);
    if (textId === thirdPlace && place !== 3) setThirdPlace(null);
    
    // Now set the new place
    if (place === 1) {
      // If another text was in first place, handle the conflict
      if (firstPlace !== null && firstPlace !== textId) {
        setFirstPlace(textId);
      } else {
        setFirstPlace(textId === firstPlace ? null : textId);
      }
    } else if (place === 2) {
      if (secondPlace !== null && secondPlace !== textId) {
        setSecondPlace(textId);
      } else {
        setSecondPlace(textId === secondPlace ? null : textId);
      }
    } else if (place === 3) {
      if (thirdPlace !== null && thirdPlace !== textId) {
        setThirdPlace(textId);
      } else {
        setThirdPlace(textId === thirdPlace ? null : textId);
      }
    }
  };
  
  // Handle comment change
  const handleCommentChange = (textId: number, comment: string) => {
    setComments({
      ...comments,
      [textId]: comment
    });
  };
  
  // Open full text modal
  const openFullTextModal = (textId: number) => {
    setFullTextModalId(textId);
  };
  
  // Close full text modal
  const closeFullTextModal = () => {
    setFullTextModalId(null);
  };
  
  // Get a preview of the text (first 200 characters)
  const getTextPreview = (content: string) => {
    const maxLength = 200;
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };
  
  // Check if we have valid selections
  const hasValidSelections = () => {
    let placesSelected = 0;
    if (firstPlace !== null) placesSelected++;
    if (secondPlace !== null) placesSelected++;
    if (thirdPlace !== null) placesSelected++;
    
    return placesSelected >= minRequiredVotes;
  };
  
  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!hasValidSelections()) {
      setError(`You must rank at least ${minRequiredVotes} different texts.`);
      return;
    }
    
    try {
      setIsLoading(true);
      setError(null);
      
      // Submit votes for ranked texts
      const votes: CreateVoteRequest[] = [];
      
      if (firstPlace !== null) {
        votes.push({
          text_id: firstPlace,
          place: 1, 
          comment: comments[firstPlace] || '',
          is_ai_vote: false
        });
      }
      
      if (secondPlace !== null) {
        votes.push({
          text_id: secondPlace,
          place: 2,
          comment: comments[secondPlace] || '',
          is_ai_vote: false
        });
      }
      
      if (thirdPlace !== null) {
        votes.push({
          text_id: thirdPlace,
          place: 3,
          comment: comments[thirdPlace] || '',
          is_ai_vote: false
        });
      }
      
      // Submit comments for any unranked texts
      texts.forEach(text => {
        if (
          text.id !== firstPlace && 
          text.id !== secondPlace && 
          text.id !== thirdPlace &&
          comments[text.id]
        ) {
          votes.push({
            text_id: text.id,
            place: null,
            comment: comments[text.id],
            is_ai_vote: false
          });
        }
      });
      
      // Submit each vote
      for (const vote of votes) {
        console.log('Submitting vote:', vote);
        await submitVote(contestId, vote);
      }
      
      setIsLoading(false);
      setSuccess('Votes submitted successfully!');
      
      // Close the modal
      onSuccess();
    } catch (err: any) {
      console.error('Error submitting votes:', err);
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to submit votes. Please try again.';
      setError(errorMessage);
      setIsLoading(false);
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Judge Contest Submissions</h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
          {error}
        </div>
      )}
      
      {success && (
        <div className="mb-4 p-3 bg-green-50 text-green-700 rounded-md">
          {success}
        </div>
      )}
      
      {isLoadingExistingVotes ? (
        <div className="mb-4 p-3 bg-blue-50 text-blue-700 rounded-md">
          Loading your existing votes...
        </div>
      ) : existingVotes.length > 0 ? (
        <div className="mb-4 p-3 bg-blue-50 text-blue-700 rounded-md">
          <p className="font-medium">You have previously voted in this contest.</p>
          <p className="text-sm">You can modify your votes below. Your previous selections are pre-filled.</p>
        </div>
      ) : (
        <div className="mb-4 p-3 bg-green-50 text-green-700 rounded-md">
          <p className="font-medium">This is your first time voting in this contest.</p>
          <p className="text-sm">Please rank your top {minRequiredVotes} choices and provide comments.</p>
        </div>
      )}
      
      <p className="mb-4 text-gray-600">
        Please rank your top {minRequiredVotes} choices and provide comments for each text.
      </p>
      
      <form onSubmit={handleSubmit}>
        <div className="space-y-8">
          {texts.map((text) => (
            <div key={text.id} className="border-b pb-6">
              <h3 className="text-lg font-semibold mb-2">{text.title}</h3>
              
              <div className="prose prose-sm max-w-none mb-4">
                <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded">
                  {getTextPreview(text.content)}
                </pre>
                
                <button
                  type="button"
                  onClick={() => openFullTextModal(text.id)}
                  className="mt-2 text-sm text-indigo-600 hover:text-indigo-800"
                >
                  Show Full Content
                </button>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ranking
                </label>
                {/* Show existing vote if any */}
                {getExistingVote(text.id) && (
                  <div className="mb-2 text-sm text-blue-600 bg-blue-50 p-2 rounded">
                    {getExistingVote(text.id)?.place ? (
                      `Previously voted: ${getExistingVote(text.id)?.place === 1 ? '1st' : getExistingVote(text.id)?.place === 2 ? '2nd' : '3rd'} place`
                    ) : (
                      'Previously commented on this text'
                    )}
                  </div>
                )}
                <div className="flex space-x-4">
                  <button
                    type="button"
                    onClick={() => handlePlaceSelection(1, text.id)}
                    className={`px-3 py-1 rounded-full transition-colors ${
                      firstPlace === text.id 
                        ? 'bg-indigo-600 text-white' 
                        : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                    }`}
                  >
                    1st Place {firstPlace === text.id && '✓'}
                  </button>
                  <button
                    type="button"
                    onClick={() => handlePlaceSelection(2, text.id)}
                    className={`px-3 py-1 rounded-full transition-colors ${
                      secondPlace === text.id 
                        ? 'bg-indigo-600 text-white' 
                        : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                    }`}
                  >
                    2nd Place {secondPlace === text.id && '✓'}
                  </button>
                  <button
                    type="button"
                    onClick={() => handlePlaceSelection(3, text.id)}
                    className={`px-3 py-1 rounded-full transition-colors ${
                      thirdPlace === text.id 
                        ? 'bg-indigo-600 text-white' 
                        : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                    }`}
                  >
                    3rd Place {thirdPlace === text.id && '✓'}
                  </button>
                </div>
              </div>
              
              <div>
                <label 
                  htmlFor={`comment-${text.id}`} 
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Comment
                </label>
                <textarea
                  id={`comment-${text.id}`}
                  rows={3}
                  className="w-full p-2 border rounded-md"
                  placeholder="Share your feedback about this text..."
                  value={comments[text.id] || ''}
                  onChange={(e) => handleCommentChange(text.id, e.target.value)}
                />
              </div>
            </div>
          ))}
        </div>
        
        <div className="flex justify-end space-x-3 mt-6">
          <button
            type="button"
            className="py-2 px-4 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
            onClick={onCancel}
          >
            Cancel
          </button>
          
          <button
            type="submit"
            className="py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-indigo-300"
            disabled={!hasValidSelections() || isLoading}
          >
            {isLoading ? 'Submitting...' : 'Submit Votes'}
          </button>
        </div>
      </form>
      
      {/* Full Text Modal */}
      {fullTextModalId !== null && (
        <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full h-[80vh] flex flex-col">
            {/* Modal header */}
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <h3 className="text-xl font-bold">
                {texts.find(t => t.id === fullTextModalId)?.title || 'Text Content'}
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
                {texts.find(t => t.id === fullTextModalId)?.content}
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

export default HumanJudgingForm; 