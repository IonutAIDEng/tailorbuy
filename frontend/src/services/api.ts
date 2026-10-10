import { API_BASE_URL } from '@/constants/api';
import { storage } from './storage';

async function attemptRefresh(): Promise<string | null> {
  const refreshToken = await storage.getRefreshToken();
  if (!refreshToken) return null;

  const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) {
    await storage.clearTokens();
    return null;
  }

  const data = await res.json();
  await storage.saveTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

export async function apiRequest(
  path: string,
  options: RequestInit & { _retry?: boolean } = {}
): Promise<Response> {
  const token = await storage.getAccessToken();

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> | undefined),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  // On 401, attempt a silent token refresh and retry the original request once
  if (res.status === 401 && !options._retry) {
    const newToken = await attemptRefresh();
    if (newToken) {
      return apiRequest(path, { ...options, _retry: true });
    }
    // Refresh failed — tokens cleared, caller handles the 401 (AuthContext will redirect)
  }

  return res;
}
