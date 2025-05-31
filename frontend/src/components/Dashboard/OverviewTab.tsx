import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import QuickActions from './QuickActions';

interface OverviewTabProps {
  dashboardData: any;
  textsCount: number;
  contestsCount: number;
  agentsCount: number;
}

const OverviewTab: React.FC<OverviewTabProps> = ({
  dashboardData,
  textsCount,
  contestsCount,
  agentsCount
}) => {
  const { user } = useAuth();

  return (
    <div>
      <h2 className="text-xl font-medium mb-6">Dashboard Overview</h2>
      
      {/* Quick Actions Component */}
      <div className="mb-8">
        <QuickActions 
          hasTexts={textsCount > 0}
          hasContests={contestsCount > 0}
          hasAgents={agentsCount > 0}
          urgentActions={dashboardData?.urgent_actions || []}
          textCount={textsCount}
          contestCount={contestsCount}
          agentCount={agentsCount}
        />
      </div>

      {/* Urgent actions section */}
      {dashboardData?.urgent_actions && dashboardData.urgent_actions.length > 0 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                You have <span className="font-medium">{dashboardData.urgent_actions.length} urgent action{dashboardData.urgent_actions.length === 1 ? '' : 's'}</span> pending.
              </p>
              <ul className="mt-2 text-sm text-yellow-700">
                {dashboardData.urgent_actions.map((action: any, index: number) => (
                  <li key={index} className="mt-1">
                    • <Link to={`/contests/${action.contest_id}`} className="underline hover:text-yellow-900">
                      Judge contest: {action.contest_title}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="font-medium text-gray-700">Credit Balance</h3>
          <p className="text-2xl font-bold text-indigo-600">
            {user?.credits !== undefined ? `${user.credits} credits` : 'Loading...'}
          </p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="font-medium text-gray-700">My Contests</h3>
          <p className="text-2xl font-bold text-indigo-600">{contestsCount}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="font-medium text-gray-700">My Texts</h3>
          <p className="text-2xl font-bold text-indigo-600">{textsCount}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="font-medium text-gray-700">AI Agents</h3>
          <p className="text-2xl font-bold text-indigo-600">{agentsCount}</p>
        </div>
      </div>
    </div>
  );
};

export default OverviewTab; 