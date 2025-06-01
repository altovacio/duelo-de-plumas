import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useResponsive } from '../../utils/responsive';
import WelcomeModal from '../Onboarding/WelcomeModal';

const Header: React.FC = () => {
  const { user, isAuthenticated, isAdmin } = useAuth();
  const navigate = useNavigate();
  const { isMobile } = useResponsive();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);

  const handleUsernameClick = () => {
    navigate('/profile');
    setIsMobileMenuOpen(false);
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  const handleHelpClick = () => {
    setShowHelpModal(true);
    setIsMobileMenuOpen(false);
  };

  // Navigation items for authenticated users
  const navItems = [
    { name: 'Home', path: '/', showAlways: true },
    { name: 'Contests', path: '/contests', showAlways: true },
    { name: 'Dashboard', path: '/dashboard', requireAuth: true },
    { name: 'Admin', path: '/admin', requireAuth: true, requireAdmin: true },
    { name: 'Onboarding', path: '/onboarding', requireAuth: true },
  ];

  const visibleNavItems = navItems.filter(item => {
    if (item.showAlways) return true;
    if (item.requireAuth && !isAuthenticated) return false;
    if (item.requireAdmin && !isAdmin()) return false;
    return true;
  });

  return (
    <>
      <header className="bg-indigo-600 text-white sticky top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link 
              to="/" 
              className="text-xl font-bold hover:text-indigo-200 transition-colors"
              onClick={closeMobileMenu}
            >
              Duelo de Plumas
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-1">
              {visibleNavItems.map((item) => (
                <Link
                  key={item.name}
                  to={item.path}
                  className="px-3 py-2 rounded-md text-sm font-medium hover:bg-indigo-500 transition-colors"
                >
                  {item.name}
                </Link>
              ))}
              
              {/* Help button for desktop */}
              {isAuthenticated && (
                <button
                  onClick={handleHelpClick}
                  className="px-3 py-2 rounded-md text-sm font-medium hover:bg-indigo-500 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:ring-offset-2 focus:ring-offset-indigo-600"
                  title="Help & Tour"
                >
                  ?
                </button>
              )}
              
              {/* User actions for desktop */}
              {isAuthenticated ? (
                <button
                  onClick={handleUsernameClick}
                  className="px-3 py-2 rounded-md text-sm font-medium hover:bg-indigo-500 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:ring-offset-2 focus:ring-offset-indigo-600"
                >
                  {user?.username} {user?.credits !== undefined && `(${user.credits})`}
                </button>
              ) : (
                <div className="flex items-center space-x-1">
                  <Link
                    to="/login"
                    className="px-3 py-2 rounded-md text-sm font-medium hover:bg-indigo-500 transition-colors"
                  >
                    Login
                  </Link>
                  <Link
                    to="/register"
                    className="px-3 py-2 rounded-md text-sm font-medium hover:bg-indigo-500 transition-colors"
                  >
                    Register
                  </Link>
                </div>
              )}
            </nav>

            {/* Mobile hamburger button */}
            <button
              onClick={toggleMobileMenu}
              className="md:hidden p-2 rounded-md hover:bg-indigo-500 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:ring-offset-2 focus:ring-offset-indigo-600"
              aria-label="Toggle mobile menu"
            >
              <svg
                className={`w-6 h-6 transition-transform duration-200 ${isMobileMenuOpen ? 'rotate-90' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                {isMobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>

          {/* Mobile Navigation Menu */}
          {isMobileMenuOpen && (
            <div className="md:hidden bg-indigo-700 border-t border-indigo-500">
              <div className="px-2 pt-2 pb-3 space-y-1">
                {/* Navigation items */}
                {visibleNavItems.map((item) => (
                  <Link
                    key={item.name}
                    to={item.path}
                    onClick={closeMobileMenu}
                    className="block px-3 py-2 rounded-md text-base font-medium hover:bg-indigo-600 transition-colors"
                  >
                    {item.name}
                  </Link>
                ))}
                
                {/* Help button for mobile */}
                {isAuthenticated && (
                  <button
                    onClick={handleHelpClick}
                    className="block w-full text-left px-3 py-2 rounded-md text-base font-medium hover:bg-indigo-600 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:ring-offset-2 focus:ring-offset-indigo-700"
                  >
                    Help & Tour
                  </button>
                )}
                
                {/* User actions for mobile */}
                {isAuthenticated ? (
                  <div className="border-t border-indigo-500 pt-3 mt-3">
                    <button
                      onClick={handleUsernameClick}
                      className="block w-full text-left px-3 py-2 rounded-md text-base font-medium hover:bg-indigo-600 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:ring-offset-2 focus:ring-offset-indigo-700"
                    >
                      {user?.username} {user?.credits !== undefined && `(${user.credits})`}
                    </button>
                  </div>
                ) : (
                  <div className="border-t border-indigo-500 pt-3 mt-3 space-y-1">
                    <Link
                      to="/login"
                      onClick={closeMobileMenu}
                      className="block px-3 py-2 rounded-md text-base font-medium hover:bg-indigo-600 transition-colors"
                    >
                      Login
                    </Link>
                    <Link
                      to="/register"
                      onClick={closeMobileMenu}
                      className="block px-3 py-2 rounded-md text-base font-medium hover:bg-indigo-600 transition-colors"
                    >
                      Register
                    </Link>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Help Modal */}
      <WelcomeModal 
        isOpen={showHelpModal}
        onClose={() => setShowHelpModal(false)}
        isFirstLogin={false}
      />
    </>
  );
};

export default Header; 