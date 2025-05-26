import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

interface ProtectedRouteProps {
  requireAdmin?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ requireAdmin = false }) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  // Show loading state while checking authentication
  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  // If not authenticated, redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // For admin routes, wait for user data to load before making the decision
  if (requireAdmin) {
    // If user data hasn't loaded yet, show loading
    if (!user) {
      return <div className="flex items-center justify-center min-h-screen">Loading user data...</div>;
    }
    
    // Now we can safely check admin status
    if (!user.is_admin) {
      console.log('Admin route access denied:', { 
        requireAdmin, 
        user: { id: user.id, username: user.username, is_admin: user.is_admin },
        location: location.pathname 
      });
      return <Navigate to="/dashboard" replace />;
    }
  }

  // Render the child routes
  return <Outlet />;
};

export default ProtectedRoute; 