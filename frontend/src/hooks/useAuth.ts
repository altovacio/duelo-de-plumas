import { useEffect, useState, useRef } from 'react';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';

export const useAuth = () => {
  const { 
    user, 
    tokens, 
    isAuthenticated, 
    isLoading, 
    error,
    login: storeLogin,
    register: storeRegister,
    logout: storeLogout,
    loadUser,
    clearError
  } = useAuthStore();

  const navigate = useNavigate();
  const hasAttemptedLoad = useRef(false);

  // Load user data when component using this hook mounts if tokens exist
  useEffect(() => {
    if (tokens && !user && !isLoading && !hasAttemptedLoad.current) {
      hasAttemptedLoad.current = true;
      loadUser();
    }
  }, [tokens, user, isLoading]);
  
  // Simple method to check if user is admin
  const isAdmin = (): boolean => {
    return !!user?.is_admin;
  };
  
  // Handle login and redirect
  const handleLogin = async (username: string, password: string, redirectTo: string = '/dashboard'): Promise<void> => {
    setIsSubmitting(true);
    try {
      // Call the store login function
      await storeLogin(username, password);
      
      // Check authentication state after login attempt
      const currentState = useAuthStore.getState();
      if (!currentState.error && currentState.isAuthenticated) {
        // Add a small delay to ensure the UI updates before navigation
        setTimeout(() => {
          navigate(redirectTo);
        }, 300);
      }
    } catch (err) {
      console.error("Login error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Handle registration and redirect
  const handleRegister = async (username: string, email: string, password: string, redirectTo: string = '/dashboard'): Promise<void> => {
    setIsSubmitting(true);
    try {
      // Call the store register function
      await storeRegister(username, email, password);
      
      // Check authentication state after registration attempt
      const currentState = useAuthStore.getState();
      if (!currentState.error && currentState.isAuthenticated) {
        // Add a small delay to ensure the UI updates before navigation
        setTimeout(() => {
          navigate(redirectTo);
        }, 300);
      }
    } catch (err) {
      console.error("Registration error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Handle logout and redirect to login page
  const handleLogout = async (): Promise<void> => {
    try {
      await storeLogout();
      navigate('/login');
    } catch (err) {
      console.error("Logout error:", err);
      // Still navigate even if API logout fails
      navigate('/login');
    }
  };

  // Local state for login/register form submission
  const [isSubmitting, setIsSubmitting] = useState(false);

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    isAdmin,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    clearError,
    isSubmitting
  };
}; 