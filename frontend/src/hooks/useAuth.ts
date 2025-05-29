import { useEffect, useState, useRef } from 'react';
import { useAuthStore } from '../store/authStore';
import { useNavigate, useLocation } from 'react-router-dom';

export const useAuth = () => {
  const { 
    user, 
    tokens, 
    isAuthenticated, 
    isLoading, 
    error,
    isFirstLogin,
    login: storeLogin,
    register: storeRegister,
    logout: storeLogout,
    loadUser,
    clearError
  } = useAuthStore();

  const navigate = useNavigate();
  const location = useLocation();
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

  // Smart redirect logic
  const getRedirectPath = (isFirstLogin: boolean): string => {
    // For first-time users, always go to home to trigger onboarding
    if (isFirstLogin) {
      return '/';
    }

    // Check if there's a redirect path in location state (from protected routes)
    const from = (location.state as any)?.from?.pathname;
    if (from && from !== '/login' && from !== '/register') {
      return from;
    }

    // Check current path to determine best redirect
    const currentPath = location.pathname;
    
    // If they're on auth pages, redirect based on context
    if (currentPath === '/login' || currentPath === '/register') {
      // Check if they were trying to access a specific page
      const urlParams = new URLSearchParams(location.search);
      const redirectTo = urlParams.get('redirect');
      if (redirectTo && redirectTo !== '/login' && redirectTo !== '/register') {
        return redirectTo;
      }
      
      // Default to home for returning users (dashboard is too overwhelming as first page)
      return '/';
    }

    // If they're already on a valid page, stay there
    return currentPath;
  };
  
  // Handle login and redirect
  const handleLogin = async (username: string, password: string, fallbackRedirect: string = '/'): Promise<void> => {
    setIsSubmitting(true);
    try {
      // Call the store login function
      await storeLogin(username, password);
      
      // Check authentication state after login attempt
      const currentState = useAuthStore.getState();
      
      if (!currentState.error && currentState.isAuthenticated) {
        const redirectPath = getRedirectPath(currentState.isFirstLogin);
        
        // Add a small delay to ensure the UI updates before navigation
        setTimeout(() => {
          navigate(redirectPath, { replace: true });
        }, 300);
      }
    } catch (err) {
      console.error("Login error in useAuth:", err);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Handle registration and redirect
  const handleRegister = async (username: string, email: string, password: string, fallbackRedirect: string = '/'): Promise<void> => {
    setIsSubmitting(true);
    try {
      // Call the store register function
      await storeRegister(username, email, password);
      
      // Check authentication state after registration attempt
      const currentState = useAuthStore.getState();
      
      if (!currentState.error && currentState.isAuthenticated) {
        // New registrations should always go to home for onboarding
        const redirectPath = '/';
        
        // Add a small delay to ensure the UI updates before navigation
        setTimeout(() => {
          navigate(redirectPath, { replace: true });
        }, 300);
      }
    } catch (err) {
      console.error("Registration error in useAuth:", err);
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
    isFirstLogin,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    clearError,
    isSubmitting
  };
}; 