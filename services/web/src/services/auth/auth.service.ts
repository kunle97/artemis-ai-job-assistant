/**
 * Auth service layer for account creation and authentication-related API calls.
 */

import axios from 'axios';
import { httpClient } from '../http/client';

export interface RegisterUserPayload {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}

export interface LoginUserPayload {
  email: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface SessionUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

interface ApiErrorBody {
  detail?: string;
}

export async function registerUser(payload: RegisterUserPayload): Promise<void> {
  try {
    await httpClient.post('/auth/register', payload);
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail?.trim();

      if (status === 409 || status === 400) {
        const normalized = (detail ?? '').toLowerCase();
        if (normalized.includes('email') || normalized.includes('already')) {
          throw new Error('An account with this email address already exists. Try signing in instead.');
        }
        throw new Error(detail || 'Registration failed. Please check your details and try again.');
      }

      if (status) {
        throw new Error(detail || `Registration failed with status ${status}.`);
      }
    }

    throw new Error('Unable to connect to the server. Please try again.');
  }
}

export async function loginUser(payload: LoginUserPayload): Promise<AuthTokens> {
  try {
    const body = new URLSearchParams();
    body.set('username', payload.email);
    body.set('password', payload.password);

    const response = await httpClient.post<AuthTokens>('/auth/login', body, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    return response.data;
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail?.trim();

      if (status === 401) {
        throw new Error('Authentication failed after registration. Please sign in manually.');
      }

      if (status) {
        throw new Error(detail || `Sign in failed with status ${status}.`);
      }
    }

    throw new Error('Unable to sign in after registration. Please try signing in manually.');
  }
}

export async function signInUser(payload: LoginUserPayload): Promise<AuthTokens> {
  try {
    const body = new URLSearchParams();
    body.set('username', payload.email);
    body.set('password', payload.password);

    const response = await httpClient.post<AuthTokens>('/auth/login', body, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    return response.data;
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail?.trim();

      if (status === 401) {
        throw new Error('Invalid email or password. Please try again.');
      }

      if (status === 429) {
        throw new Error('Too many sign-in attempts. Please wait a moment and try again.');
      }

      if (status) {
        throw new Error(detail || `Sign in failed with status ${status}.`);
      }
    }

    throw new Error('Unable to connect to the server. Please try again.');
  }
}

export async function refreshAccessToken(refreshToken: string): Promise<AuthTokens> {
  try {
    const response = await httpClient.post<AuthTokens>('/auth/refresh', {
      refresh_token: refreshToken,
    });

    return response.data;
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail?.trim();
      if (status === 401) {
        throw new Error('Session expired. Please sign in again.');
      }
      if (status) {
        throw new Error(detail || `Session refresh failed with status ${status}.`);
      }
    }

    throw new Error('Unable to refresh your session. Please sign in again.');
  }
}

export async function getCurrentSession(accessToken: string): Promise<SessionUser> {
  try {
    const response = await httpClient.get<SessionUser>('/auth/session', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    return response.data;
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      if (status === 401) {
        throw new Error('Not authenticated.');
      }
      if (status) {
        throw new Error(`Session check failed with status ${status}.`);
      }
    }

    throw new Error('Unable to verify current session.');
  }
}

export async function logoutUser(accessToken: string, refreshToken?: string): Promise<void> {
  try {
    await httpClient.post(
      '/auth/logout',
      refreshToken ? { refresh_token: refreshToken } : undefined,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      },
    );
  } catch {
    // Ignore logout API failures so local tokens can still be cleared on client side.
  }
}

export function storeAuthTokens(tokens: AuthTokens): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('access_token', tokens.access_token);
  localStorage.setItem('refresh_token', tokens.refresh_token);
}

export function getStoredAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

export function getStoredRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('refresh_token');
}

export function clearStoredTokens(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

export function redirectToLandingOnSessionExpired(): void {
  if (typeof window === 'undefined') return;
  clearStoredTokens();
  window.location.replace('/sign-in?reason=session-expired');
}
