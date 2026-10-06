// When testing on a physical Android device replace with your laptop's local IP:
// e.g. http://192.168.1.100:8000
export const API_BASE_URL = 'http://10.0.2.2:8000';

export const USER_ID = 1;

export const ENDPOINTS = {
  search: '/search',
  preferences: (userId: number) => `/preferences/${userId}`,
} as const;
