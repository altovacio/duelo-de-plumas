import React, { ReactNode, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import WelcomeModal from '../Onboarding/WelcomeModal';

interface MainLayoutProps {
  children: ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { user, isAuthenticated, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [showHelpModal, setShowHelpModal] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="bg-indigo-600 text-white">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <Link to="/" className="text-xl font-bold">Duelo de Plumas</Link>
          
          <nav className="flex space-x-4">
            <Link to="/" className="px-2 py-1 rounded hover:bg-indigo-500">Home</Link>
            <Link to="/contests" className="px-2 py-1 rounded hover:bg-indigo-500">Contests</Link>
            
            {isAuthenticated ? (
              <>
                <Link to="/dashboard" className="px-2 py-1 rounded hover:bg-indigo-500">Dashboard</Link>
                <Link to="/ai-writer" className="px-2 py-1 rounded hover:bg-indigo-500">AI Writer</Link>
                {isAdmin() && (
                  <Link to="/admin" className="px-2 py-1 rounded hover:bg-indigo-500">Admin</Link>
                )}
                <button 
                  onClick={() => setShowHelpModal(true)}
                  className="px-2 py-1 rounded hover:bg-indigo-500 focus:outline-none"
                  title="Help & Tour"
                >
                  ?
                </button>
                <button 
                  onClick={handleLogout}
                  className="px-2 py-1 rounded hover:bg-indigo-500 focus:outline-none"
                >
                  Logout
                </button>
                <span className="px-2 py-1">
                  {user?.username} {user?.credits !== undefined && `(${user.credits} credits)`}
                </span>
              </>
            ) : (
              <>
                <Link to="/login" className="px-2 py-1 rounded hover:bg-indigo-500">Login</Link>
                <Link to="/register" className="px-2 py-1 rounded hover:bg-indigo-500">Register</Link>
              </>
            )}
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-grow">
        <div className="container mx-auto px-4 py-8">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 text-gray-600">
        <div className="container mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <div>
              <p>&copy; {new Date().getFullYear()} Duelo de Plumas. All rights reserved.</p>
            </div>
            <div className="flex space-x-4">
              <Link to="/about" className="hover:text-indigo-600">About</Link>
              <Link to="/terms" className="hover:text-indigo-600">Terms</Link>
              <Link to="/privacy" className="hover:text-indigo-600">Privacy</Link>
            </div>
          </div>
        </div>
      </footer>

      {/* Help Modal */}
      <WelcomeModal 
        isOpen={showHelpModal}
        onClose={() => setShowHelpModal(false)}
        isFirstLogin={false}
      />
    </div>
  );
};

export default MainLayout; 