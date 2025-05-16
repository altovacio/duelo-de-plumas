import { useEffect } from 'react';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';

export const useAuth = () => {
  const { 
    user, 
    tokens, 
    isAuthenticated, 
    isLoading, 
    error,
    login,
    register,
    logout,
    loadUser,
    clearError
  } = useAuthStore();

  const navigate = useNavigate();

  // Load user data when component using this hook mounts if tokens exist
  useEffect(() => {
    if (tokens && !user && !isLoading) {
      loadUser();
    }
  }, [tokens, user, isLoading, loadUser]);
  
  // Simple method to check if user is admin
  const isAdmin = (): boolean => {
    return !!user?.is_admin;
  };
  
  // Handle login and redirect
  const handleLogin = async (username: string, password: string, redirectTo: string = '/dashboard'): Promise<void> => {
    await login(username, password);
    const { error } = useAuthStore.getState();
    if (!error) {
      navigate(redirectTo);
    }
  };
  
  // Handle registration and redirect
  const handleRegister = async (username: string, email: string, password: string, redirectTo: string = '/dashboard'): Promise<void> => {
    await register(username, email, password);
    const { error } = useAuthStore.getState();
    if (!error) {
      navigate(redirectTo);
    }
  };
  
  // Handle logout and redirect to login page
  const handleLogout = async (): Promise<void> => {
    await logout();
    navigate('/login');
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    isAdmin,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    clearError
  };
}; 