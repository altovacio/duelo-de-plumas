import React, { useState, useEffect } from 'react';
import { Text } from '../../services/textService';
import { submitVote, CreateVoteRequest } from '../../services/voteService';

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
  // State for storing place (ranking) selections
  const [firstPlace, setFirstPlace] = useState<number | null>(null);
  const [secondPlace, setSecondPlace] = useState<number | null>(null);
  const [thirdPlace, setThirdPlace] = useState<number | null>(null);
  
  // State for storing comments
  const [comments, setComments] = useState<Record<number, string>>({});
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Calculate minimum required votes based on texts count
  const minRequiredVotes = Math.min(3, texts.length);
  
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
          comment: comments[firstPlace] || ''
        });
      }
      
      if (secondPlace !== null) {
        votes.push({
          text_id: secondPlace,
          place: 2,
          comment: comments[secondPlace] || ''
        });
      }
      
      if (thirdPlace !== null) {
        votes.push({
          text_id: thirdPlace,
          place: 3,
          comment: comments[thirdPlace] || ''
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
            comment: comments[text.id]
          });
        }
      });
      
      // Submit each vote
      for (const vote of votes) {
        await submitVote(contestId, vote);
      }
      
      setIsLoading(false);
      onSuccess();
    } catch (err: any) {
      console.error('Error submitting votes:', err);
      setError(err.response?.data?.message || 'Failed to submit votes. Please try again.');
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
      
      <p className="mb-4 text-gray-600">
        Please rank your top {minRequiredVotes} choices and provide comments for each text.
      </p>
      
      <form onSubmit={handleSubmit}>
        <div className="space-y-8">
          {texts.map((text) => (
            <div key={text.id} className="border-b pb-6">
              <h3 className="text-lg font-semibold mb-2">{text.title}</h3>
              
              <div className="prose prose-sm max-w-none mb-4">
                <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded">{text.content}</pre>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ranking
                </label>
                <div className="flex space-x-4">
                  <button
                    type="button"
                    onClick={() => handlePlaceSelection(1, text.id)}
                    className={`px-3 py-1 rounded-full ${
                      firstPlace === text.id 
                        ? 'bg-indigo-600 text-white' 
                        : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                    }`}
                  >
                    1st Place
                  </button>
                  <button
                    type="button"
                    onClick={() => handlePlaceSelection(2, text.id)}
                    className={`px-3 py-1 rounded-full ${
                      secondPlace === text.id 
                        ? 'bg-indigo-600 text-white' 
                        : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                    }`}
                  >
                    2nd Place
                  </button>
                  <button
                    type="button"
                    onClick={() => handlePlaceSelection(3, text.id)}
                    className={`px-3 py-1 rounded-full ${
                      thirdPlace === text.id 
                        ? 'bg-indigo-600 text-white' 
                        : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                    }`}
                  >
                    3rd Place
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
    </div>
  );
};

export default HumanJudgingForm; 