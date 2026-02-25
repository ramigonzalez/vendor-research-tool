/** Base API URL from environment variable */
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/** Fetch wrapper with base URL */
export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText}`);
  }
  return response.json();
}

