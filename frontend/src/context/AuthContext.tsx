import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { apiRequest } from '../services/api';
import { storage } from '../services/storage';

export interface AuthUser {
  id: number;
  email: string;
  nickname: string | null;
}

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, nickname?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadUser = useCallback(async () => {
    const token = await storage.getAccessToken();
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const res = await apiRequest('/auth/me');
      if (res.ok) {
        setUser(await res.json());
      } else {
        await storage.clearTokens();
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = async (email: string, password: string): Promise<void> => {
    const res = await apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(typeof err?.detail === 'string' ? err.detail : 'Autentificare eșuată');
    }
    const data = await res.json();
    await storage.saveTokens(data.access_token, data.refresh_token);
    await loadUser();
  };

  const register = async (email: string, password: string, nickname?: string): Promise<void> => {
    const res = await apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, nickname: nickname ?? null }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(typeof err?.detail === 'string' ? err.detail : 'Înregistrare eșuată');
    }
    const data = await res.json();
    await storage.saveTokens(data.access_token, data.refresh_token);
    await loadUser();
  };

  const logout = async (): Promise<void> => {
    try {
      const refreshToken = await storage.getRefreshToken();
      if (refreshToken) {
        await apiRequest('/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      }
    } catch { /* network error during logout is acceptable */ }
    await storage.clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout, refreshUser: loadUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
