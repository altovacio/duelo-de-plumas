import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

// This would typically come from an API call
interface Contest {
  id: number;
  title: string;
  description: string;
  participantCount: number;
  lastModified: string;
  endDate?: string;
  type: 'public' | 'private';
  status: 'open' | 'evaluation' | 'closed';
}

const HomePage: React.FC = () => {
  const [recentOpenContests, setRecentOpenContests] = useState<Contest[]>([]);
  const [recentClosedContests, setRecentClosedContests] = useState<Contest[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    // This would be replaced with an actual API call
    const fetchContests = () => {
      setIsLoading(true);
      
      // Simulate API delay
      setTimeout(() => {
        // Sample data - would come from backend in a real app
        const openContests: Contest[] = [
          {
            id: 1,
            title: "Summer Poetry Challenge",
            description: "Share your best summer-inspired poems.",
            participantCount: 12,
            lastModified: "2023-06-15",
            endDate: "2023-07-30",
            type: "public",
            status: "open"
          },
          {
            id: 2,
            title: "Short Story Festival",
            description: "Submit your short stories under 5000 words.",
            participantCount: 24,
            lastModified: "2023-06-10",
            type: "public",
            status: "open"
          }
        ];
        
        const closedContests: Contest[] = [
          {
            id: 3,
            title: "Spring Fiction Competition",
            description: "Fiction stories inspired by spring themes.",
            participantCount: 35,
            lastModified: "2023-05-25",
            endDate: "2023-06-01",
            type: "public",
            status: "closed"
          },
          {
            id: 4,
            title: "Microfiction Challenge",
            description: "Tell your story in less than 100 words.",
            participantCount: 48,
            lastModified: "2023-05-15",
            endDate: "2023-05-30",
            type: "public",
            status: "closed"
          }
        ];
        
        setRecentOpenContests(openContests);
        setRecentClosedContests(closedContests);
        setIsLoading(false);
      }, 1000);
    };
    
    fetchContests();
  }, []);

  const ContestCard = ({ contest }: { contest: Contest }) => (
    <div className="border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow bg-white">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-semibold">{contest.title}</h3>
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
      <p className="text-sm text-gray-600 mb-3 line-clamp-2">{contest.description}</p>
      <div className="flex justify-between text-xs text-gray-500">
        <span>{contest.participantCount} participants</span>
        <span>Last updated: {new Date(contest.lastModified).toLocaleDateString()}</span>
      </div>
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

  return (
    <div className="space-y-10">
      {/* Hero section */}
      <section className="text-center py-16 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg">
        <h1 className="text-4xl font-bold mb-4">Welcome to Duelo de Plumas</h1>
        <p className="text-xl mb-8">The literary contest platform for writers and AI enthusiasts</p>
        <div className="flex justify-center space-x-4">
          <Link 
            to="/contests" 
            className="px-6 py-3 rounded-lg bg-white text-indigo-600 font-medium hover:bg-gray-100 transition-colors"
          >
            Browse Contests
          </Link>
          <Link 
            to="/dashboard" 
            className="px-6 py-3 rounded-lg bg-indigo-700 text-white font-medium hover:bg-indigo-800 transition-colors"
          >
            My Dashboard
          </Link>
        </div>
      </section>

      {/* Recent Open Contests */}
      <section>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">Recently Opened Contests</h2>
          <Link to="/contests?status=open" className="text-indigo-600 hover:text-indigo-800">
            View all →
          </Link>
        </div>
        
        {isLoading ? (
          <div className="text-center py-8">Loading contests...</div>
        ) : recentOpenContests.length === 0 ? (
          <div className="text-center py-8 bg-gray-50 rounded-lg">
            <p className="text-gray-500">No open contests available at the moment.</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-4">
            {recentOpenContests.map(contest => (
              <ContestCard key={contest.id} contest={contest} />
            ))}
          </div>
        )}
      </section>

      {/* Recent Closed Contests */}
      <section>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">Recently Closed Contests</h2>
          <Link to="/contests?status=closed" className="text-indigo-600 hover:text-indigo-800">
            View all →
          </Link>
        </div>
        
        {isLoading ? (
          <div className="text-center py-8">Loading contests...</div>
        ) : recentClosedContests.length === 0 ? (
          <div className="text-center py-8 bg-gray-50 rounded-lg">
            <p className="text-gray-500">No recently closed contests available.</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-4">
            {recentClosedContests.map(contest => (
              <ContestCard key={contest.id} contest={contest} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default HomePage; 