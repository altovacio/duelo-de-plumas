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
    isFirstLogin: boolean;
    setIsFirstLogin: (isFirst: boolean) => void;
  }
>((set, get) => ({
  ...initialState,
  isFirstLogin: false,
  
  // Login action
  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const { user, tokens, isFirstLogin } = await apiLogin({ username, password });
      
      set({ 
        user, 
        tokens, 
        isAuthenticated: true, 
        isLoading: false, 
        error: null,
        isFirstLogin: isFirstLogin || false
      });
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
      // New registrations are always first login
      set({ 
        user, 
        tokens, 
        isAuthenticated: true, 
        isLoading: false, 
        error: null,
        isFirstLogin: true 
      });
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
      set({ 
        user: null, 
        tokens: null, 
        isAuthenticated: false, 
        isLoading: false,
        isFirstLogin: false 
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Logout failed';
      set({ error: errorMessage, isLoading: false });
      // Still clear user data even if API call fails
      set({ 
        user: null, 
        tokens: null, 
        isAuthenticated: false,
        isFirstLogin: false 
      });
    }
  },

  // Load user data from stored tokens
  loadUser: async () => {
    const tokens = get().tokens;
    if (!tokens) {
      set({ isAuthenticated: false, isLoading: false });
      return;
    }

    set({ isLoading: true, error: null });
    try {
      const user = await getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      console.error('AuthStore: Load user error', error);
      // If token is invalid, clear auth state
      set({ 
        user: null, 
        tokens: null, 
        isAuthenticated: false, 
        isLoading: false,
        isFirstLogin: false 
      });
    }
  },

  // Utility actions
  setUser: (user: User | null) => set({ user }),
  setTokens: (tokens: AuthTokens | null) => set({ tokens, isAuthenticated: !!tokens }),
  setError: (error: string | null) => set({ error }),
  clearError: () => set({ error: null }),
  setIsFirstLogin: (isFirst: boolean) => set({ isFirstLogin: isFirst }),
})); 