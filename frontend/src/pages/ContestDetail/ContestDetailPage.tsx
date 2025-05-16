import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

// Contest interface (expanded from the list page)
interface Contest {
  id: number;
  title: string;
  description: string;
  fullDescription?: string; // Markdown content
  creator: {
    id: number;
    username: string;
  };
  participantCount: number;
  textCount: number;
  lastModified: string;
  createdAt: string;
  endDate?: string;
  type: 'public' | 'private';
  status: 'open' | 'evaluation' | 'closed';
  isPasswordProtected: boolean;
  minRequiredVotes?: number;
  restrictJudgesFromParticipating?: boolean;
  restrictMultipleSubmissions?: boolean;
}

// Text interface for submissions
interface Text {
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
  createdAt: string;
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
    const { isAuthenticated } = useAuth(); // Removed unused 'user' variable
    const [contest, setContest] = useState<Contest | null>(null);
    const [texts, setTexts] = useState<Text[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [password, setPassword] = useState<string>('');
    const [isPasswordCorrect, setIsPasswordCorrect] = useState<boolean>(false);
    const [passwordError, setPasswordError] = useState<string | null>(null);
    const [showPasswordModal, setShowPasswordModal] = useState<boolean>(false);

  useEffect(() => {
    // This would be replaced with an actual API call
    const fetchContestDetails = () => {
      setIsLoading(true);
      
      // Simulate API delay
      setTimeout(() => {
        // Mock data - would come from backend in a real app
        const mockContest: Contest = {
          id: parseInt(id || '1'),
          title: "Summer Poetry Challenge",
          description: "Share your best summer-inspired poems.",
          fullDescription: "# Summer Poetry Challenge\n\nWelcome to our annual Summer Poetry Challenge! This year, we're looking for poems that capture the essence of summer.\n\n## Guidelines\n\n- Poems should be between 10 and 40 lines\n- Any form of poetry is acceptable\n- Submissions must be original and previously unpublished\n- One entry per participant\n\n## Judging Criteria\n\n- Originality (30%)\n- Technical skill (30%)\n- Emotional impact (40%)\n\nWe look forward to reading your summer-inspired creations!",
          creator: {
            id: 1,
            username: "poetrylover"
          },
          participantCount: 12,
          textCount: 15,
          lastModified: "2023-06-15",
          createdAt: "2023-06-01",
          endDate: "2023-07-30",
          type: "public", // Change to private to test password protection
          status: "open", // Change to "evaluation" or "closed" to test different states
          isPasswordProtected: false,
          minRequiredVotes: 3,
          restrictJudgesFromParticipating: true,
          restrictMultipleSubmissions: true
        };
        
        // Mock text submissions
        const mockTexts: Text[] = [
          {
            id: 101,
            title: "Summer Breeze",
            content: "Summer breeze makes me feel fine\nBlowing through the jasmine in my mind...",
            createdAt: "2023-06-05"
          },
          {
            id: 102,
            title: "Ocean Waves",
            content: "The gentle rhythm of the ocean waves\nCrashing on the shore under summer rays...",
            createdAt: "2023-06-07"
          },
          {
            id: 103,
            title: "Sunset Dreams",
            content: "Crimson skies at day's end\nWhisper promises of tomorrow...",
            createdAt: "2023-06-10"
          }
        ];
        
        // For evaluation or closed status, show authors and votes
        if (mockContest.status === 'evaluation' || mockContest.status === 'closed') {
          mockTexts.forEach(text => {
            text.author = {
              id: 200 + Math.floor(Math.random() * 100),
              username: `user${Math.floor(Math.random() * 100)}`
            };
            
            // For closed status, add voting results
            if (mockContest.status === 'closed') {
              text.votes = [
                {
                  rank: Math.floor(Math.random() * 3) + 1,
                  judge: {
                    id: 300,
                    username: "judge1",
                    isAI: false
                  },
                  comment: "Beautiful imagery and rhythm."
                },
                {
                  rank: Math.floor(Math.random() * 3) + 1,
                  judge: {
                    id: 301,
                    username: "AI Judge",
                    isAI: true,
                    aiModel: "GPT-4"
                  },
                  comment: "Excellent use of metaphor and sensory language."
                }
              ];
            }
          });
        }
        
        setContest(mockContest);
        setTexts(mockTexts);
        
        // If contest is public or we've already verified the password, show content
        if (mockContest.type === 'public' || isPasswordCorrect) {
          setIsPasswordCorrect(true);
        } else {
          setShowPasswordModal(true);
        }
        
        setIsLoading(false);
      }, 1000);
    };
    
    fetchContestDetails();
  }, [id, isPasswordCorrect]);

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

  // Calculate points and ranking (for closed contests)
  const getContestRanking = () => {
    if (!texts || texts.length === 0 || contest?.status !== 'closed') {
      return [];
    }
    
    const textScores = texts.map(text => {
      const points = text.votes?.reduce((total: number, vote) => {
        // 3 points for 1st place, 2 for 2nd, 1 for 3rd
        return total + (4 - vote.rank);
      }, 0) || 0;
      
      return {
        ...text,
        points
      };
    });
    
    // Sort by points, highest first
    return textScores.sort((a, b) => ((b.points as number) || 0) - ((a.points as number) || 0));
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
            <span className="font-medium">Created:</span> {new Date(contest.createdAt).toLocaleDateString()}
          </div>
          <div>
            <span className="font-medium">Last updated:</span> {new Date(contest.lastModified).toLocaleDateString()}
          </div>
          {contest.endDate && (
            <div>
              <span className="font-medium">End date:</span> {new Date(contest.endDate).toLocaleDateString()}
            </div>
          )}
          <div>
            <span className="font-medium">Participants:</span> {contest.participantCount}
          </div>
          <div>
            <span className="font-medium">Submissions:</span> {contest.textCount}
          </div>
        </div>
      </div>
      
      {/* Contest Full Description */}
      <div className="bg-white p-6 rounded-lg shadow-sm mb-8">
        <h2 className="text-xl font-bold mb-4">Contest Details</h2>
        <div className="prose max-w-none">
          {/* This would use react-markdown to render Markdown content */}
          <pre className="whitespace-pre-wrap">{contest.fullDescription}</pre>
        </div>
      </div>
      
      {/* Contest State-specific Content */}
      {contest.status === 'open' && (
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h2 className="text-xl font-bold mb-4">Submit Your Entry</h2>
          
          {isAuthenticated ? (
            <div>
              <p className="mb-4">Ready to participate? Submit your text to this contest.</p>
              <Link 
                to={`/dashboard/texts/new?contestId=${contest.id}`}
                className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Submit Text
              </Link>
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
      
      {(contest.status === 'evaluation' || contest.status === 'closed') && (
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h2 className="text-xl font-bold mb-4">
            {contest.status === 'evaluation' ? 'Submissions Under Evaluation' : 'Contest Results'}
          </h2>
          
          {texts.length === 0 ? (
            <p className="text-gray-500">No texts have been submitted to this contest.</p>
          ) : (
            <div className="space-y-6">
              {contest.status === 'closed' ? (
                // Display results for closed contests
                getContestRanking().map((text: Text & { points?: number }, index: number) => (
                  <div key={text.id} className="border-b pb-6 last:border-b-0">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="text-lg font-semibold">{text.title}</h3>
                        <p className="text-sm text-gray-600">
                          by {text.author?.username} • Submitted on {new Date(text.createdAt).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full font-medium">
                        {index === 0 ? '🥇 First Place' : 
                         index === 1 ? '🥈 Second Place' : 
                         index === 2 ? '🥉 Third Place' : `${index + 1}th Place`} 
                         ({text.points} points)
                      </div>
                    </div>
                    
                    <div className="prose prose-sm max-w-none mb-4">
                      <pre className="whitespace-pre-wrap">{text.content}</pre>
                    </div>
                    
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="font-medium mb-2">Judge Comments</h4>
                      {text.votes?.map((vote: {
                        rank: number;
                        judge: {
                          id: number;
                          username: string;
                          isAI: boolean;
                          aiModel?: string;
                        };
                        comment: string;
                      }, vIndex: number) => (
                        <div key={vIndex} className="mb-2 last:mb-0">
                          <p className="text-sm font-medium">
                            {vote.judge.username} 
                            {vote.judge.isAI && <span className="text-gray-500"> (AI: {vote.judge.aiModel})</span>}
                            <span className="font-normal text-gray-500"> • Ranked #{vote.rank}</span>
                          </p>
                          <p className="text-sm">{vote.comment}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              ) : (
                // Display anonymized texts for evaluation phase
                texts.map((text: Text) => (
                  <div key={text.id} className="border-b pb-6 last:border-b-0">
                    <h3 className="text-lg font-semibold mb-2">{text.title}</h3>
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap">{text.content}</pre>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ContestDetailPage; 