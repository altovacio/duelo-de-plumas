import React, { useState, useEffect } from 'react';
import { getContestVotes, Vote } from '../../services/voteService';
import { Text } from '../../services/textService';

interface ContestResultsProps {
  contestId: number;
  texts: Text[];
}

interface TextWithScore extends Text {
  score: number;
  votes: Vote[];
}

interface JudgeInfo {
  id: number;
  name: string;
  isAI: boolean;
}

const ContestResults: React.FC<ContestResultsProps> = ({
  contestId,
  texts
}) => {
  const [votes, setVotes] = useState<Vote[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeJudgeFilter, setActiveJudgeFilter] = useState<number | 'all'>('all');
  const [judges, setJudges] = useState<JudgeInfo[]>([]);
  const [activeJudgeType, setActiveJudgeType] = useState<'all' | 'human' | 'ai'>('all');
  const [expandedTextId, setExpandedTextId] = useState<number | null>(null);
  
  useEffect(() => {
    const fetchVotes = async () => {
      try {
        setIsLoading(true);
        const votesData = await getContestVotes(contestId);
        setVotes(votesData);
        
        // Extract unique judges from votes
        const uniqueJudges = new Map<number, JudgeInfo>();
        votesData.forEach(vote => {
          if (!uniqueJudges.has(vote.judge_id)) {
            uniqueJudges.set(vote.judge_id, {
              id: vote.judge_id,
              name: `Judge ${vote.judge_id}`,
              isAI: vote.judge_type === 'ai'
            });
          }
        });
        
        setJudges(Array.from(uniqueJudges.values()));
        setIsLoading(false);
      } catch (err) {
        console.error('Error fetching votes:', err);
        setError('Failed to load voting results. Please try again.');
        setIsLoading(false);
      }
    };
    
    fetchVotes();
  }, [contestId]);
  
  // Calculate rankings based on votes
  const calculateRankings = (): TextWithScore[] => {
    // Filter votes by judge type
    let filteredVotes = votes;
    
    if (activeJudgeType !== 'all') {
      filteredVotes = votes.filter(vote => 
        (activeJudgeType === 'ai' && vote.judge_type === 'ai') ||
        (activeJudgeType === 'human' && vote.judge_type !== 'ai')
      );
    }
    
    // Further filter by specific judge if selected
    if (activeJudgeFilter !== 'all') {
      filteredVotes = filteredVotes.filter(vote => vote.judge_id === activeJudgeFilter);
    }
    
    // Map to track scores for each text
    const textScores = new Map<number, { score: number, votes: Vote[] }>();
    
    // Initialize all texts with 0 score
    texts.forEach(text => {
      textScores.set(text.id, { score: 0, votes: [] });
    });
    
    // Calculate scores: 3 points for 1st place, 2 for 2nd, 1 for 3rd
    filteredVotes.forEach(vote => {
      if (vote.place) {
        const textData = textScores.get(vote.text_id);
        if (textData) {
          // 4 - vote.place gives 3 points for 1st place, 2 for 2nd, 1 for 3rd
          textData.score += 4 - vote.place;
          textData.votes.push(vote);
        }
      }
    });
    
    // Convert to array and merge with text data
    return texts.map(text => ({
      ...text,
      score: textScores.get(text.id)?.score || 0,
      votes: textScores.get(text.id)?.votes || []
    })).sort((a, b) => b.score - a.score); // Sort by score, highest first
  };
  
  const toggleExpandedText = (textId: number) => {
    setExpandedTextId(expandedTextId === textId ? null : textId);
  };
  
  const rankedTexts = calculateRankings();
  
  if (isLoading) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">Loading contest results...</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-50 text-red-700 p-4 rounded-md">
        {error}
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Contest Results</h2>
      
      {/* Judge type filter */}
      <div className="mb-4">
        <h3 className="text-md font-medium mb-2">Judge Type</h3>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setActiveJudgeType('all')}
            className={`px-3 py-1 rounded-full ${
              activeJudgeType === 'all'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
            }`}
          >
            All Judges
          </button>
          <button
            onClick={() => setActiveJudgeType('human')}
            className={`px-3 py-1 rounded-full ${
              activeJudgeType === 'human'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
            }`}
          >
            Human Judges
          </button>
          <button
            onClick={() => setActiveJudgeType('ai')}
            className={`px-3 py-1 rounded-full ${
              activeJudgeType === 'ai'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
            }`}
          >
            AI Judges
          </button>
        </div>
      </div>
      
      {/* Specific judge filter */}
      {judges.length > 0 && (
        <div className="mb-6">
          <h3 className="text-md font-medium mb-2">Filter by Judge</h3>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setActiveJudgeFilter('all')}
              className={`px-3 py-1 rounded-full ${
                activeJudgeFilter === 'all'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
              }`}
            >
              All Judges
            </button>
            
            {judges
              .filter(judge => 
                activeJudgeType === 'all' || 
                (activeJudgeType === 'ai' && judge.isAI) || 
                (activeJudgeType === 'human' && !judge.isAI)
              )
              .map(judge => (
                <button
                  key={judge.id}
                  onClick={() => setActiveJudgeFilter(judge.id)}
                  className={`px-3 py-1 rounded-full flex items-center ${
                    activeJudgeFilter === judge.id
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                  }`}
                >
                  {judge.name}
                  {judge.isAI && (
                    <span className={`ml-1 text-xs ${activeJudgeFilter === judge.id ? 'bg-indigo-500 text-white' : 'bg-blue-200 text-blue-800'} rounded px-1`}>
                      AI
                    </span>
                  )}
                </button>
              ))}
          </div>
        </div>
      )}
      
      {/* Results podium for top 3 */}
      {rankedTexts.length > 0 && (
        <div className="mb-8">
          <h3 className="text-md font-medium mb-4">Podium</h3>
          
          <div className="flex justify-center items-end my-6 h-48">
            {/* Second place */}
            {rankedTexts.length > 1 && (
              <div className="w-1/3 mx-2">
                <div className="flex flex-col items-center">
                  <div className="text-xl font-bold">🥈</div>
                  <div className="bg-gray-200 w-full h-32 flex items-center justify-center rounded-t-lg">
                    <div className="text-center p-2">
                      <div className="font-bold">{rankedTexts[1].title}</div>
                      <div className="text-sm text-gray-600">
                        {rankedTexts[1].author || 'Anonymous'}
                      </div>
                      <div className="text-sm font-medium mt-1">
                        {rankedTexts[1].score} pts
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* First place */}
            <div className="w-1/3 mx-2">
              <div className="flex flex-col items-center">
                <div className="text-xl font-bold">🥇</div>
                <div className="bg-amber-200 w-full h-40 flex items-center justify-center rounded-t-lg">
                  <div className="text-center p-2">
                    <div className="font-bold text-lg">{rankedTexts[0].title}</div>
                    <div className="text-sm text-gray-600">
                      {rankedTexts[0].author || 'Anonymous'}
                    </div>
                    <div className="text-sm font-medium mt-1">
                      {rankedTexts[0].score} pts
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Third place */}
            {rankedTexts.length > 2 && (
              <div className="w-1/3 mx-2">
                <div className="flex flex-col items-center">
                  <div className="text-xl font-bold">🥉</div>
                  <div className="bg-amber-100 w-full h-24 flex items-center justify-center rounded-t-lg">
                    <div className="text-center p-2">
                      <div className="font-bold">{rankedTexts[2].title}</div>
                      <div className="text-sm text-gray-600">
                        {rankedTexts[2].author || 'Anonymous'}
                      </div>
                      <div className="text-sm font-medium mt-1">
                        {rankedTexts[2].score} pts
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Detailed results list */}
      <div>
        <h3 className="text-md font-medium mb-4">All Results</h3>
        
        {rankedTexts.length === 0 ? (
          <p className="text-gray-500">No votes have been submitted yet.</p>
        ) : (
          <div className="space-y-6">
            {rankedTexts.map((text, index) => (
              <div key={text.id} className="border-b pb-6 last:border-b-0">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="text-lg font-semibold">{text.title}</h3>
                    <p className="text-sm text-gray-600">
                      by {text.author || 'Anonymous'}
                    </p>
                  </div>
                  <div className="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full font-medium">
                    {index === 0 ? '🥇 First Place' : 
                     index === 1 ? '🥈 Second Place' : 
                     index === 2 ? '🥉 Third Place' : `${index + 1}th Place`} 
                     ({text.score} points)
                  </div>
                </div>
                
                <div className="prose prose-sm max-w-none mb-4">
                  {text.content === 'TEXTO RETIRADO' ? (
                    <div className="p-4 bg-gray-100 text-gray-500 italic rounded">
                      This text has been withdrawn by the author.
                    </div>
                  ) : (
                    <pre className="whitespace-pre-wrap bg-gray-50 p-3 rounded-md">{text.content}</pre>
                  )}
                </div>
                
                <div className="mb-2">
                  <button
                    onClick={() => toggleExpandedText(text.id)}
                    className="text-indigo-600 hover:text-indigo-800 text-sm font-medium flex items-center"
                  >
                    <span>{expandedTextId === text.id ? 'Hide Comments' : 'Show Judge Comments'}</span>
                    <svg 
                      className={`ml-1 w-4 h-4 transform transition-transform ${expandedTextId === text.id ? 'rotate-180' : ''}`} 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                    </svg>
                  </button>
                </div>
                
                {expandedTextId === text.id && text.votes.length > 0 && (
                  <div className="bg-gray-50 p-4 rounded-lg mt-2">
                    <h4 className="font-medium mb-2">Judge Comments</h4>
                    <div className="space-y-3">
                      {text.votes.map((vote, vIndex) => (
                        <div key={vIndex} className="bg-white p-3 rounded border border-gray-200">
                          <div className="flex justify-between items-center mb-1">
                            <div className="font-medium flex items-center">
                              Judge {vote.judge_id}
                              {vote.judge_type === 'ai' && (
                                <span className="ml-1 text-xs bg-blue-100 text-blue-800 rounded px-1">
                                  AI
                                </span>
                              )}
                            </div>
                            <div className="text-sm text-gray-500">
                              {vote.place ? `Ranked #${vote.place}` : 'Unranked'}
                            </div>
                          </div>
                          <div className="text-sm text-gray-700 whitespace-pre-line">
                            {vote.comment || 'No comment provided.'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ContestResults;