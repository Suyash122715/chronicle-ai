import { create } from "zustand";
import { User } from "@/types/auth";
import authService from "@/services/authService";

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isInitialized: boolean;
  isLoading: boolean;
  setAuth: (token: string, user?: User | null) => void;
  setUser: (user: User) => void;
  clearAuth: () => void;
  initializeAuth: () => Promise<void>;
}

const TOKEN_KEY = "chronicle_access_token";

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  user: null,
  isAuthenticated: false,
  isInitialized: false,
  isLoading: false,

  setAuth: (token: string, user: User | null = null) => {
    if (typeof window !== "undefined") {
      localStorage.setItem(TOKEN_KEY, token);
    }
    set({
      token,
      user,
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
    });
  },

  setUser: (user: User) => {
    set({ user });
  },

  clearAuth: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(TOKEN_KEY);
    }
    set({
      token: null,
      user: null,
      isAuthenticated: false,
      isInitialized: true,
      isLoading: false,
    });
  },

  initializeAuth: async () => {
    if (typeof window === "undefined") return;
    if (get().isInitialized && get().user) return;

    const storedToken = localStorage.getItem(TOKEN_KEY);
    if (!storedToken) {
      set({
        token: null,
        user: null,
        isAuthenticated: false,
        isInitialized: true,
        isLoading: false,
      });
      return;
    }

    set({ token: storedToken, isLoading: true });

    try {
      const user = await authService.getCurrentUser();
      set({
        token: storedToken,
        user,
        isAuthenticated: true,
        isInitialized: true,
        isLoading: false,
      });
    } catch {
      // Invalid/expired token
      if (typeof window !== "undefined") {
        localStorage.removeItem(TOKEN_KEY);
      }
      set({
        token: null,
        user: null,
        isAuthenticated: false,
        isInitialized: true,
        isLoading: false,
      });
    }
  },
}));

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}
