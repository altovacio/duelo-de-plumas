import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

type RegisterFormData = {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
};

const RegisterPage: React.FC = () => {
  const { register: registerUser, error, clearError, isSubmitting, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  
  const { 
    register, 
    handleSubmit, 
    watch,
    formState: { errors },
    setFocus
  } = useForm<RegisterFormData>();

  const password = watch('password', '');

  // Clear errors only when navigating from login page (not on every mount)
  useEffect(() => {
    // Only clear errors if we came from the login page
    const from = (location.state as any)?.from;
    if (from === '/login') {
      clearError();
    }
  }, [clearError, location.state]);

  // Redirect already authenticated users
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      const from = (location.state as any)?.from?.pathname;
      const redirectTo = from && from !== '/login' && from !== '/register' ? from : '/home';
      navigate(redirectTo, { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate, location.state]);

  // Handle successful authentication
  useEffect(() => {
    if (isAuthenticated && !error) {
      setRegistrationSuccess(true);
    }
  }, [isAuthenticated, error]);

  // Handle form submission
  const onSubmit = async (data: RegisterFormData) => {
    setRegistrationSuccess(false);
    clearError(); // Clear any previous errors
    
    try {
      await registerUser(data.username, data.email, data.password);
    } catch (err) {
      // Focus on username field for easy retry
      setTimeout(() => setFocus('username'), 100);
    }
  };

  // Get user-friendly error message for registration
  const getUserFriendlyError = (errorMsg: string | null): string => {
    if (!errorMsg) return '';
    
    const lowerError = errorMsg.toLowerCase();
    
    // Handle specific field errors from backend
    if (lowerError.includes('username error:') || lowerError.startsWith('username:')) {
      if (lowerError.includes('already exists') || lowerError.includes('taken') || lowerError.includes('duplicate')) {
        return '❌ Username already taken - This username is already registered. Please choose a different username.';
      }
      return '❌ Username issue - Please check your username and try again.';
    }
    
    if (lowerError.includes('email error:') || lowerError.startsWith('email:')) {
      if (lowerError.includes('already exists') || lowerError.includes('taken') || lowerError.includes('duplicate')) {
        return '❌ Email already registered - An account with this email address already exists. Please use a different email or try signing in instead.';
      }
      return '❌ Email issue - Please check your email address and try again.';
    }
    
    // Handle username conflicts
    if (lowerError.includes('username') && (
        lowerError.includes('exists') || lowerError.includes('taken') || lowerError.includes('already') ||
        lowerError.includes('duplicate') || lowerError.includes('unavailable') || lowerError.includes('in use')
      )) {
      return '❌ Username already taken - This username is already registered. Please choose a different username.';
    }
    
    // Handle email conflicts
    if (lowerError.includes('email') && (
        lowerError.includes('exists') || lowerError.includes('taken') || lowerError.includes('already') ||
        lowerError.includes('duplicate') || lowerError.includes('unavailable') || lowerError.includes('in use') ||
        lowerError.includes('registered')
      )) {
      return '❌ Email already registered - An account with this email address already exists. Please use a different email or try signing in instead.';
    }
    
    // Handle generic constraint errors
    if (lowerError.includes('duplicate') || lowerError.includes('constraint') || lowerError.includes('unique')) {
      if (lowerError.includes('username') || lowerError.includes('user')) {
        return '❌ Username already taken - This username is already registered. Please choose a different username.';
      }
      if (lowerError.includes('email')) {
        return '❌ Email already registered - An account with this email address already exists. Please use a different email or try signing in instead.';
      }
      return '❌ Registration conflict - The username or email you entered is already in use. Please try different values.';
    }
    
    // Handle other common errors
    if (lowerError.includes('password') && (lowerError.includes('weak') || lowerError.includes('short') || lowerError.includes('simple'))) {
      return 'Password is too weak. Please use at least 8 characters with a mix of letters, numbers, and symbols.';
    }
    
    if (lowerError.includes('invalid email') || lowerError.includes('email format')) {
      return 'Please enter a valid email address.';
    }
    
    if (lowerError.includes('400') || lowerError.includes('bad request')) {
      return 'Please check your information and try again. Make sure all fields are filled correctly.';
    }
    
    if (lowerError.includes('network error') || lowerError.includes('fetch')) {
      return 'Unable to connect to server. Please check your internet connection and try again.';
    }
    
    if (lowerError.includes('timeout')) {
      return 'Connection timeout. Please try again.';
    }
    
    // Default fallback
    return 'Unable to create account. Please try again or contact support if the problem persists.';
  };

  // Show loading if we're checking authentication status
  if (isLoading) {
    return (
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <svg className="animate-spin -ml-1 mr-3 h-8 w-8 text-indigo-600 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="mt-2 text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Or{' '}
            <Link 
              to="/login" 
              state={{ from: '/register' }}
              className="font-medium text-indigo-600 hover:text-indigo-500"
            >
              sign in to your existing account
            </Link>
          </p>
        </div>
        
        {registrationSuccess && (
          <div className="rounded-md bg-green-50 p-4 border border-green-200">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">Registration successful!</h3>
                <div className="mt-2 text-sm text-green-700">
                  Your account has been created. Redirecting to get started...
                </div>
              </div>
            </div>
          </div>
        )}
        
        {error && !registrationSuccess && (
          <div className="rounded-md bg-red-50 p-4 border border-red-200" role="alert" aria-live="polite">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3 flex-1">
                <h3 className="text-sm font-medium text-red-800">Unable to create account</h3>
                <div className="mt-2 text-sm text-red-700">
                  {getUserFriendlyError(error)}
                </div>
              </div>
              <div className="ml-auto pl-3">
                <div className="-mx-1.5 -my-1.5">
                  <button
                    type="button"
                    onClick={clearError}
                    className="inline-flex rounded-md bg-red-50 p-1.5 text-red-500 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2 focus:ring-offset-red-50"
                    aria-label="Dismiss error"
                  >
                    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">Username</label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm ${
                  error ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Choose a username"
                {...register('username', { 
                  required: 'Username is required',
                  minLength: { value: 3, message: 'Username must be at least 3 characters' },
                  pattern: { value: /^[a-zA-Z0-9_-]+$/, message: 'Username can only contain letters, numbers, underscore, and dash' }
                })}
              />
              {errors.username && (
                <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm ${
                  error ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Enter your email"
                {...register('email', { 
                  required: 'Email is required',
                  pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'Please enter a valid email address' }
                })}
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
              )}
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">Password</label>
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm ${
                  error ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Create a password"
                {...register('password', { 
                  required: 'Password is required',
                  minLength: { value: 8, message: 'Password must be at least 8 characters' }
                })}
              />
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">Confirm Password</label>
              <input
                id="confirmPassword"
                type="password"
                autoComplete="new-password"
                className={`mt-1 appearance-none relative block w-full px-3 py-2 border placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm ${
                  error ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="Confirm your password"
                {...register('confirmPassword', { 
                  required: 'Please confirm your password',
                  validate: value => value === password || 'Passwords do not match'
                })}
              />
              {errors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">{errors.confirmPassword.message}</p>
              )}
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isSubmitting || registrationSuccess}
              className={`group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white ${
                registrationSuccess 
                  ? 'bg-green-600 hover:bg-green-700 focus:ring-green-500' 
                  : 'bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500'
              } focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                (isSubmitting || registrationSuccess) ? 'opacity-70 cursor-not-allowed' : ''
              }`}
            >
              {isSubmitting ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating account...
                </span>
              ) : registrationSuccess ? (
                <span className="flex items-center">
                  <svg className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Account created!
                </span>
              ) : (
                'Create account'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RegisterPage; 