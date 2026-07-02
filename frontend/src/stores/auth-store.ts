import { create } from "zustand";
import { persist } from "zustand/middleware";
import { User } from "@/types";

interface AuthState {
  token: string | null;
  user: User | null;
  mfaToken: string | null;
  setAuth: (token: string, user: User) => void;
  setMfaToken: (mfaToken: string) => void;
  clearMfaToken: () => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      mfaToken: null,
      setAuth: (token, user) => set({ token, user, mfaToken: null }),
      setMfaToken: (mfaToken) => set({ mfaToken }),
      clearMfaToken: () => set({ mfaToken: null }),
      logout: () => set({ token: null, user: null, mfaToken: null }),
      isAuthenticated: () => !!get().token,
    }),
    {
      name: "auth-storage",
    }
  )
);
