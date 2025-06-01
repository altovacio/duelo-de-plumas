import React from 'react';
import { Link } from 'react-router-dom';
import { Contest as ContestType } from '../../services/contestService';

interface ParticipationTabProps {
  contestsData: ContestType[];
  participationContests: {
    asAuthor: ContestType[];
    asJudge: ContestType[];
    asMember: ContestType[];
  };
  isLoading: boolean;
  error: string | null;
}

const ParticipationTab: React.FC<ParticipationTabProps> = ({
  contestsData,
  participationContests,
  isLoading,
  error
}) => {
  const LoadingSpinner = () => (
    <div className="flex justify-center items-center h-32">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
    </div>
  );

  const ContestList = ({ contests, emptyMessage }: { contests: ContestType[], emptyMessage: string }) => (
    contests.length > 0 ? (
      <div className="bg-white shadow rounded-md overflow-hidden">
        <ul className="divide-y divide-gray-200">
          {contests.map(contest => (
            <li key={contest.id} className="px-4 py-3 hover:bg-gray-50">
              <div className="flex justify-between">
                <div>
                  <Link to={`/contests/${contest.id}`} className="text-indigo-600 hover:text-indigo-900 font-medium">
                    {contest.title}
                  </Link>
                  <div className="flex mt-1 space-x-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      contest.status === 'open' ? 'bg-green-100 text-green-800' :
                      contest.status === 'evaluation' ? 'bg-yellow-100 text-yellow-800' :
                       'bg-blue-100 text-blue-800'
                    }`}>
                      {contest.status && typeof contest.status === 'string' 
                        ? contest.status.charAt(0).toUpperCase() + contest.status.slice(1) 
                        : 'Unknown'}
                    </span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      contest.publicly_listed ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'
                    }`}>
                      {contest.publicly_listed ? 'Public' : 'Private'}
                    </span>
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  {contest.created_at ? new Date(contest.created_at).toLocaleDateString() : ''}
                </div>
                {contest.end_date && (
                  <div className="text-xs mt-1">
                    {(() => {
                      const now = new Date();
                      const deadline = new Date(contest.end_date);
                      const isExpired = now > deadline;
                      
                      return (
                        <div className={`inline-flex items-center px-2 py-1 rounded-full ${
                          isExpired 
                            ? 'bg-red-100 text-red-800'
                            : 'bg-orange-100 text-orange-800'
                        }`}>
                          <span className="mr-1">⏰</span>
                          <span>
                            {isExpired 
                              ? `Expired ${deadline.toLocaleDateString()}` 
                              : `Deadline: ${deadline.toLocaleDateString()}`
                            }
                          </span>
                        </div>
                      );
                    })()}
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>
    ) : (
      <p className="text-gray-500 italic">{emptyMessage}</p>
    )
  );

  const JudgeContestList = ({ contests }: { contests: ContestType[] }) => (
    contests.length > 0 ? (
      <div className="bg-white shadow rounded-md overflow-hidden">
        <ul className="divide-y divide-gray-200">
          {contests.map(contest => (
            <li key={contest.id} className="px-4 py-3 hover:bg-gray-50">
              <div className="flex justify-between">
                <div>
                  <Link to={`/contests/${contest.id}`} className="text-indigo-600 hover:text-indigo-900 font-medium">
                    {contest.title}
                  </Link>
                  <div className="flex mt-1 space-x-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      contest.status === 'open' ? 'bg-green-100 text-green-800' :
                      contest.status === 'evaluation' ? 'bg-yellow-100 text-yellow-800' :
                       'bg-blue-100 text-blue-800'
                    }`}>
                      {contest.status && typeof contest.status === 'string' 
                        ? contest.status.charAt(0).toUpperCase() + contest.status.slice(1) 
                        : 'Unknown'}
                    </span>
                    {contest.status === 'evaluation' && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        Needs Judging
                      </span>
                    )}
                  </div>
                </div>
                <Link 
                  to={`/contests/${contest.id}`} 
                  className={`text-sm font-medium ${contest.status === 'evaluation' ? 'text-red-600 hover:text-red-900' : 'text-gray-500'}`}
                >
                  {contest.status === 'evaluation' ? 'Judge Now' : 'View'}
                </Link>
              </div>
            </li>
          ))}
        </ul>
      </div>
    ) : (
      <p className="text-gray-500 italic">Not participating in any contests as a judge.</p>
    )
  );

  return (
    <div>
      <h2 className="text-xl font-medium mb-4">My Participation</h2>
      
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}
      
      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6">
          <div>
            <h3 className="font-medium text-gray-700 mb-2">Contests I created</h3>
            <ContestList 
              contests={contestsData} 
              emptyMessage="No contests created yet." 
            />
          </div>
          
          <div>
            <h3 className="font-medium text-gray-700 mb-2">Contests where I'm an author</h3>
            <ContestList 
              contests={participationContests.asAuthor} 
              emptyMessage="Not participating in any contests as an author." 
            />
          </div>
          
          <div>
            <h3 className="font-medium text-gray-700 mb-2">Contests where I'm a member</h3>
            <ContestList 
              contests={participationContests.asMember} 
              emptyMessage="Not a member of any contests." 
            />
          </div>
          
          <div>
            <h3 className="font-medium text-gray-700 mb-2">Contests where I'm a judge</h3>
            <JudgeContestList contests={participationContests.asJudge} />
          </div>
        </div>
      )}
    </div>
  );
};

export default ParticipationTab; 