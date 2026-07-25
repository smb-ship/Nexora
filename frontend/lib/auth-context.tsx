"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { authApi, ApiError, type User } from "@/lib/api";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, organizationName: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    authApi
      .me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const loggedInUser = await authApi.login({ email, password });
    setUser(loggedInUser);
  }

  async function register(email: string, password: string, organizationName: string, fullName?: string) {
    // Backend now sets auth cookies directly on /auth/register (it creates
    // the new Organization and logs the Owner in immediately), so a
    // separate login() call right after is no longer needed.
    const registeredUser = await authApi.register({
      email,
      password,
      full_name: fullName,
      organization_name: organizationName,
    });
    setUser(registeredUser);
  }

  async function logout() {
    await authApi.logout();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}