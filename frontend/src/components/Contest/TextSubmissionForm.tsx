import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Text } from '../../services/textService';
import { getUserTexts } from '../../services/textService';
import { submitTextToContest } from '../../services/contestService';

interface TextSubmissionFormProps {
  contestId: number;
  isPrivate: boolean;
  password?: string;
  onSuccess: () => void;
  onCancel: () => void;
}

const TextSubmissionForm: React.FC<TextSubmissionFormProps> = ({
  contestId,
  isPrivate,
  password,
  onSuccess,
  onCancel
}) => {
  const navigate = useNavigate();
  const [texts, setTexts] = useState<Text[]>([]);
  const [selectedTextId, setSelectedTextId] = useState<number | ''>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTexts = async () => {
      try {
        setIsLoading(true);
        const userTexts = await getUserTexts();
        setTexts(userTexts);
        setIsLoading(false);
      } catch (err) {
        console.error('Error fetching texts:', err);
        setError('Failed to load your texts. Please try again.');
        setIsLoading(false);
      }
    };

    fetchTexts();
  }, []);

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
        isPrivate ? password : undefined
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

  return (
    <div className="bg-white rounded-lg shadow p-6 max-w-lg mx-auto">
      <h2 className="text-xl font-bold mb-4">Submit Text to Contest</h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
          {error}
        </div>
      )}
      
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
            <select
              id="text-select"
              className="w-full p-2 border rounded-md"
              value={selectedTextId}
              onChange={(e) => setSelectedTextId(Number(e.target.value))}
            >
              <option value="">-- Select a text --</option>
              {texts.map((text) => (
                <option key={text.id} value={text.id}>
                  {text.title}
                </option>
              ))}
            </select>
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
              className="py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-indigo-300"
              disabled={!selectedTextId || isLoading}
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