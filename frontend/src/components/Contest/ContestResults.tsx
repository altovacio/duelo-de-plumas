import React, { useState } from 'react';
import { Text } from '../../services/textService';
import FullTextModal from '../Common/FullTextModal';

interface ContestResultsProps {
  contestId: number;
  texts: any[]; // Using any[] because this comes from ContestText with additional fields
}

interface RankedText {
  id: number;
  title: string;
  content: string;
  author: string;
  ranking?: number;
  total_points?: number;
  evaluations?: any[];
}

const ContestResults: React.FC<ContestResultsProps> = ({
  contestId,
  texts
}) => {
  const [selectedTextForModal, setSelectedTextForModal] = useState<RankedText | null>(null);
  
  // Convert and sort texts by ranking
  const rankedTexts: RankedText[] = texts
    .map(text => ({
      id: text.text_id || text.id,
      title: text.title,
      content: text.content,
      author: text.author,
      ranking: text.ranking,
      total_points: text.total_points,
      evaluations: text.evaluations
    }))
    .sort((a, b) => {
      // Sort by ranking (1st, 2nd, 3rd, etc.)
      // If no ranking, put at the end
      if (!a.ranking && !b.ranking) return 0;
      if (!a.ranking) return 1;
      if (!b.ranking) return -1;
      return a.ranking - b.ranking;
    });
  
  const getRankingDisplay = (ranking?: number) => {
    if (!ranking) return 'Unranked';
    
    const suffix = ranking === 1 ? 'st' : ranking === 2 ? 'nd' : ranking === 3 ? 'rd' : 'th';
    return `${ranking}${suffix}`;
  };

  const getRankingColor = (ranking?: number) => {
    if (!ranking) return 'bg-gray-100 text-gray-600';
    switch (ranking) {
      case 1: return 'bg-yellow-100 text-yellow-800';
      case 2: return 'bg-gray-100 text-gray-700';
      case 3: return 'bg-orange-100 text-orange-700';
      default: return 'bg-blue-50 text-blue-600';
    }
  };

  // Helper function to get preview of text content
  const getTextPreview = (content: string) => {
    const maxLength = 300;
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  const openFullTextModal = (text: RankedText) => {
    setSelectedTextForModal(text);
  };

  const closeFullTextModal = () => {
    setSelectedTextForModal(null);
  };

  if (texts.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Contest Results</h2>
        <p className="text-gray-500">No submissions were made to this contest.</p>
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Contest Results</h2>
      
      <div className="space-y-4">
        {rankedTexts.map((text, index) => (
          <div 
            key={text.id} 
            className={`border rounded-lg p-4 ${
              text.ranking === 1 ? 'border-yellow-300 bg-yellow-50' :
              text.ranking === 2 ? 'border-gray-300 bg-gray-50' :
              text.ranking === 3 ? 'border-orange-300 bg-orange-50' :
              'border-gray-200 bg-white'
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRankingColor(text.ranking)}`}>
                    {getRankingDisplay(text.ranking)}
                  </span>
                  {text.total_points !== undefined && (
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-bold">
                      {text.total_points} points
                    </span>
                  )}
                </div>
                <h3 className="text-lg font-semibold text-gray-900">{text.title}</h3>
                <p className="text-sm text-gray-600">by {text.author}</p>
              </div>
            </div>
            
            {/* Text preview */}
            <div className="mb-4">
              <div className="prose prose-sm max-w-none">
                <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded text-sm">
                  {getTextPreview(text.content)}
                </pre>
                {text.content.length > 300 && (
                  <button
                    onClick={() => openFullTextModal(text)}
                    className="mt-2 text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                  >
                    Read Full Text
                  </button>
                )}
              </div>
            </div>
            
            {/* Judge evaluations */}
            {text.evaluations && text.evaluations.length > 0 && (
              <div className="bg-blue-50 p-4 rounded-md">
                <h4 className="font-medium text-gray-900 mb-3">Judge Evaluations</h4>
                <div className="space-y-3">
                  {text.evaluations.map((evaluation, evalIndex) => (
                    <div key={evalIndex} className="bg-white p-3 rounded border">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-900">
                          {evaluation.judge_identifier}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700">{evaluation.comment}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {rankedTexts.every(text => !text.ranking) && (
        <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
          <p className="text-yellow-800">
            <strong>Note:</strong> No rankings have been calculated yet. 
            This typically happens when no judges have voted in the contest.
          </p>
        </div>
      )}

      {/* Full Text Modal */}
      <FullTextModal
        isOpen={selectedTextForModal !== null}
        onClose={closeFullTextModal}
        title={selectedTextForModal?.title || ''}
        content={selectedTextForModal?.content || ''}
        author={selectedTextForModal?.author}
      />
    </div>
  );
};

export default ContestResults;