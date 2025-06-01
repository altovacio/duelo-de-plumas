import React, { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import Header from './Header';

interface MainLayoutProps {
  children: ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <Header />

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
    </div>
  );
};

export default MainLayout; 