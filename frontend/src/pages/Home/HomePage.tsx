import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getContests, Contest as ContestServiceType } from '../../services/contestService';
import ContestCard from '../../components/Contest/ContestCard';
import WelcomeModal from '../../components/Onboarding/WelcomeModal';
import { useAuth } from '../../hooks/useAuth';
import { useAuthStore } from '../../store/authStore';

const HomePage: React.FC = () => {
  const [recentOpenContests, setRecentOpenContests] = useState<ContestServiceType[]>([]);
  const [recentClosedContests, setRecentClosedContests] = useState<ContestServiceType[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [showWelcomeModal, setShowWelcomeModal] = useState<boolean>(false);
  
  const { isAuthenticated, user } = useAuth();
  const { isFirstLogin, setIsFirstLogin } = useAuthStore();

  // Check for first login and show welcome modal
  useEffect(() => {
    if (isAuthenticated && user && isFirstLogin) {
      setShowWelcomeModal(true);
    }
  }, [isAuthenticated, user, isFirstLogin]);

  // Handle closing the welcome modal
  const handleCloseWelcomeModal = () => {
    setShowWelcomeModal(false);
    // Clear the first login flag so it doesn't show again
    setIsFirstLogin(false);
  };

  useEffect(() => {
    const fetchContestsData = async () => {
      setIsLoading(true);
      try {
        const allContests = await getContests({});
        // Filter and sort contests for display
        // Example: take top 2 most recently updated open and closed contests
        const openContests = allContests
          .filter(c => c.status === 'open')
          .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
          .slice(0, 2);

        const closedContests = allContests
          .filter(c => c.status === 'closed')
          .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
          .slice(0, 2);

        setRecentOpenContests(openContests);
        setRecentClosedContests(closedContests);
      } catch (error) {
        console.error("Error fetching contests:", error);
        // Handle error state if needed, e.g., show an error message
      }
      setIsLoading(false);
    };
    
    fetchContestsData();
  }, []);

  return (
    <div className="space-y-10">
      {/* Welcome Modal for first-time users */}
      <WelcomeModal 
        isOpen={showWelcomeModal}
        onClose={handleCloseWelcomeModal}
        isFirstLogin={isFirstLogin}
      />

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