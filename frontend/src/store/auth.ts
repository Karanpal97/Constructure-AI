import { create } from "zustand";
import { api, UserProfile } from "@/lib/api";

interface AuthState {
  user: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  
  initialize: () => Promise<void>;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  setToken: (token: string) => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,
  error: null,

  initialize: async () => {
    try {
      set({ isLoading: true, error: null });
      
      const verification = await api.verifyToken();
      
      if (verification.valid) {
        const user = await api.getCurrentUser();
        set({ user, isAuthenticated: true, isLoading: false });
      } else {
        set({ user: null, isAuthenticated: false, isLoading: false });
      }
    } catch (error) {
      console.error("Auth initialization error:", error);
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  login: async () => {
    try {
      set({ isLoading: true, error: null });
      const { authorization_url } = await api.getLoginUrl();
      window.location.href = authorization_url;
    } catch (error) {
      console.error("Login error:", error);
      set({ 
        error: "Failed to initiate login. Please try again.", 
        isLoading: false 
      });
    }
  },

  logout: async () => {
    try {
      await api.logout();
      set({ user: null, isAuthenticated: false });
    } catch (error) {
      console.error("Logout error:", error);
      // Still clear local state even if API call fails
      api.clearToken();
      set({ user: null, isAuthenticated: false });
    }
  },

  setToken: async (token: string) => {
    try {
      set({ isLoading: true, error: null });
      api.setToken(token);
      
      const user = await api.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      console.error("Token setting error:", error);
      api.clearToken();
      set({ 
        user: null, 
        isAuthenticated: false, 
        isLoading: false,
        error: "Authentication failed. Please try again.",
      });
    }
  },

  clearError: () => set({ error: null }),
}));

