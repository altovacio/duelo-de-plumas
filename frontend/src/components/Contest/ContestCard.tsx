import React from 'react';
import { Link } from 'react-router-dom';
import { Contest } from '../../services/contestService';

interface ContestCardProps {
  contest: Contest;
}

const ContestCard: React.FC<ContestCardProps> = ({ contest }) => {
  return (
    <div className="border rounded-lg p-3 md:p-4 shadow-sm hover:shadow-md transition-shadow bg-white">
      <div className="flex flex-col md:flex-row md:justify-between md:items-start mb-2 space-y-2 md:space-y-0">
        <h3 className="text-base md:text-lg font-semibold pr-2">{contest.title}</h3>
        <div className="flex flex-wrap gap-1 md:gap-2">
          {/* Visibility badge */}
          <div 
            className={`text-xs px-2 py-1 rounded-full ${
              contest.publicly_listed
                ? 'bg-blue-100 text-blue-800' 
                : 'bg-purple-100 text-purple-800'
            }`}
          >
            {contest.publicly_listed ? 'Public' : 'Private'}
          </div>
          
          {/* Password protection badge */}
          {contest.password_protected && (
            <div className="text-xs px-2 py-1 rounded-full bg-yellow-100 text-yellow-800">
              🔒 Password
            </div>
          )}
          
          {/* Status badge */}
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
      <p className="text-sm text-gray-600 mb-3 line-clamp-2">{contest.description}</p>
      <div className="flex flex-col md:flex-row md:justify-between text-xs text-gray-500 space-y-1 md:space-y-0">
        <span>{contest.participant_count || 0} participants</span>
        <span>Created: {new Date(contest.created_at).toLocaleDateString()}</span>
      </div>
      {contest.end_date && (
        <div className="mt-2 text-xs">
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
      <div className="mt-3">
        <Link 
          to={`/contests/${contest.id}`} 
          className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
        >
          View details →
        </Link>
      </div>
    </div>
  );
};

export default ContestCard; 