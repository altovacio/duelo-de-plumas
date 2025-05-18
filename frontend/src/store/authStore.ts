import { create } from 'zustand';
import { AuthState, User, AuthTokens } from '../types/auth';
import { login as apiLogin, register as apiRegister, logout as apiLogout, getCurrentUser } from '../services/authService';
import { getTokens } from '../utils/tokenUtils';

const initialState: AuthState = {
  user: null,
  tokens: getTokens(),
  isAuthenticated: !!getTokens(),
  isLoading: false,
  error: null,
};

export const useAuthStore = create<
  AuthState & {
    login: (username: string, password: string) => Promise<void>;
    register: (username: string, email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    loadUser: () => Promise<void>;
    setUser: (user: User | null) => void;
    setTokens: (tokens: AuthTokens | null) => void;
    setError: (error: string | null) => void;
    clearError: () => void;
  }
>((set, get) => ({
  ...initialState,
  
  // Login action
  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const { user, tokens } = await apiLogin({ username, password });
      set({ user, tokens, isAuthenticated: true, isLoading: false, error: null });
    } catch (error) {
      console.error('AuthStore: Login error', error);
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      set({ error: errorMessage, isLoading: false, isAuthenticated: false });
    }
  },
  
  // Register action
  register: async (username: string, email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const { user, tokens } = await apiRegister({ username, email, password });
      set({ user, tokens, isAuthenticated: true, isLoading: false, error: null });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed';
      set({ error: errorMessage, isLoading: false, isAuthenticated: false });
    }
  },
  
  // Logout action
  logout: async () => {
    set({ isLoading: true });
    try {
      await apiLogout();
      set({ user: null, tokens: null, isAuthenticated: false, isLoading: false });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Logout failed';
      set({ error: errorMessage, isLoading: false });
      // Still clear user data even if API call fails
      set({ user: null, tokens: null, isAuthenticated: false });
    }
  },
  
  // Load user data
  loadUser: async () => {
    const { tokens } = get();
    if (!tokens) {
      set({ isAuthenticated: false });
      return;
    }
    
    set({ isLoading: true });
    try {
      const user = await getCurrentUser();
      if (user) {
        set({ user, isAuthenticated: true, isLoading: false });
      } else {
        set({ user: null, isAuthenticated: false, isLoading: false });
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load user';
      set({ 
        error: errorMessage, 
        user: null, 
        isAuthenticated: false, 
        isLoading: false 
      });
    }
  },
  
  // Utility functions to update state
  setUser: (user) => set({ user }),
  setTokens: (tokens) => set({ tokens, isAuthenticated: !!tokens }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
})); 