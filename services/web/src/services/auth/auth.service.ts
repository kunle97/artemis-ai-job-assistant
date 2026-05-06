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
