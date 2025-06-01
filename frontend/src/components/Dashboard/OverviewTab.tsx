import React from 'react';
import { Link } from 'react-router-dom';
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
        <div className="space-y-4 mb-6">
          {/* Regular urgent actions */}
          {dashboardData.urgent_actions.filter((action: any) => action.action_type !== 'expired_deadline').length > 0 && (
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-yellow-700">
                    You have urgent actions pending.
                  </p>
                  <ul className="mt-2 text-sm text-yellow-700">
                    {dashboardData.urgent_actions
                      .filter((action: any) => action.action_type !== 'expired_deadline')
                      .map((action: any, index: number) => (
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
          
          {/* Expired deadline actions */}
          {dashboardData.urgent_actions.filter((action: any) => action.action_type === 'expired_deadline').length > 0 && (
            <div className="bg-red-50 border-l-4 border-red-400 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    Contest Deadlines Have Passed
                  </h3>
                  <div className="mt-2 text-sm text-red-700">
                    <p className="mb-2">
                      The following contests have expired deadlines but are still accepting submissions. 
                      Consider moving them to evaluation phase:
                    </p>
                    <ul className="space-y-2">
                      {dashboardData.urgent_actions
                        .filter((action: any) => action.action_type === 'expired_deadline')
                        .map((action: any, index: number) => (
                          <li key={index} className="flex items-center justify-between bg-red-100 rounded p-2">
                            <span>
                              <strong>{action.contest_title}</strong>
                            </span>
                            <div className="flex space-x-2">
                              <Link 
                                to={`/contests/${action.contest_id}`} 
                                className="text-red-800 underline hover:text-red-900 text-xs"
                              >
                                View Contest
                              </Link>
                              <Link 
                                to={`/dashboard?tab=contests`} 
                                className="bg-red-600 text-white px-2 py-1 rounded text-xs hover:bg-red-700"
                              >
                                Manage
                              </Link>
                            </div>
                          </li>
                        ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default OverviewTab; 