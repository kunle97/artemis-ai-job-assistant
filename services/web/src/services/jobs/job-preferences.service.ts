/**
 * Job preferences service layer for /jobs/preferences API calls.
 */

import axios from 'axios';
import { httpClient } from '../http/client';
import { redirectToLandingOnSessionExpired } from '../auth/auth.service';

interface ApiErrorBody {
  detail?: string;
}

export interface JobPreferences {
  target_titles: string[];
  positive_keywords: string[];
  negative_keywords: string[];
  locations: string[];
  remote_only: boolean;
  salary_min: number | null;
  enabled_sources: string[];
}

function buildAuthHeader(token: string) {
  return {
    Authorization: `Bearer ${token}`,
  };
}

export async function getJobPreferences(token: string): Promise<JobPreferences> {
  try {
    const response = await httpClient.get<JobPreferences>('/jobs/preferences', {
      headers: buildAuthHeader(token),
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      if (status === 401) {
        redirectToLandingOnSessionExpired();
        throw new Error('Session expired. Redirecting to home.');
      }
      if (status) {
        throw new Error(`Failed to load job preferences with status ${status}.`);
      }
    }
    throw new Error('Unable to load job preferences right now.');
  }
}

export async function updateJobPreferences(
  token: string,
  payload: JobPreferences,
): Promise<JobPreferences> {
  try {
    const response = await httpClient.put<JobPreferences>('/jobs/preferences', payload, {
      headers: buildAuthHeader(token),
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail?.trim();
      if (status === 401) {
        redirectToLandingOnSessionExpired();
        throw new Error('Session expired. Redirecting to home.');
      }
      if (status) {
        throw new Error(detail || `Failed to save job preferences with status ${status}.`);
      }
    }
    throw new Error('Unable to save job preferences right now.');
  }
}
