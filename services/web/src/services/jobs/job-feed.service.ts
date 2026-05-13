/**
 * Job feed service layer for feed scan, feed retrieval, manual search, and feed status updates.
 */

import axios from 'axios';
import { httpClient } from '../http/client';

interface ApiErrorBody {
  detail?: string;
}

export type JobFeedStatus = 'new' | 'seen' | 'saved' | 'dismissed';
export type JobFeedSortOrder = 'newest' | 'salary_high' | 'salary_low' | 'fit_high';

export interface JobItem {
  id: string;
  source: string;
  source_job_id: string;
  title: string;
  company_name: string;
  location: string | null;
  workplace_type: string | null;
  description: string | null;
  apply_url: string;
  salary_min: number | null;
  salary_max: number | null;
  currency: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  application_id?: string | null;
  fit_score?: number | null;
  fit_recommendation?: 'apply_immediately' | 'worth_applying' | 'apply_if_specific_reason' | 'recommend_against' | null;
  fit_score_confidence?: 'high' | 'low' | null;
  feed_status?: JobFeedStatus | null;
}

export interface FeedPageResponse {
  total: number;
  skip: number;
  limit: number;
  has_next: boolean;
  prevUrl: string | null;
  next_url: string | null;
  jobs: JobItem[];
}

export interface SearchJobsPayload {
  source: string;
  board_token?: string;
  company_name?: string;
  query?: string;
  location?: string;
}

export interface ScanFeedResponse {
  new_jobs_found: number;
  discovery_run_id?: string | null;
  discovery_candidates_found?: number | null;
  discovery_promoted_count?: number | null;
  discovery_skipped_count?: number | null;
}

export interface CreateJobPayload {
  apply_url: string;
}

function buildAuthHeader(token: string) {
  return {
    Authorization: `Bearer ${token}`,
  };
}

export async function scanJobFeed(token: string): Promise<ScanFeedResponse> {
  try {
    const response = await httpClient.post<ScanFeedResponse>(
      '/jobs/feed/scan',
      undefined,
      { headers: buildAuthHeader(token) },
    );
    return response.data;
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail?.trim();
      if (status === 401) {
        throw new Error('Session expired. Please sign in again.');
      }
      if (status) {
        throw new Error(detail || `Feed scan failed with status ${status}.`);
      }
    }
    throw new Error('Unable to scan job feed right now.');
  }
}

export async function getJobFeed(
  token: string,
  skip = 0,
  limit = 20,
  query?: string,
  sort: JobFeedSortOrder = 'newest',
  sources?: string[],
): Promise<FeedPageResponse> {
  try {
    const response = await httpClient.get<FeedPageResponse>('/jobs/feed', {
      headers: buildAuthHeader(token),
      params: { skip, limit, query, sort, ...(sources?.length ? { sources: sources.join(',') } : {}) },
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      if (status === 401) {
        throw new Error('Session expired. Please sign in again.');
      }
      if (status) {
        throw new Error(`Failed to load feed with status ${status}.`);
      }
    }
    throw new Error('Unable to load job feed right now.');
  }
}

export async function searchJobs(
  token: string,
  payload: SearchJobsPayload,
  skip = 0,
  limit = 20,
): Promise<FeedPageResponse> {
  try {
    const response = await httpClient.post<FeedPageResponse>('/jobs/search', payload, {
      headers: buildAuthHeader(token),
      params: { skip, limit },
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail?.trim();
      if (status === 400) {
        throw new Error(detail || 'Search request is invalid.');
      }
      if (status === 401) {
        throw new Error('Session expired. Please sign in again.');
      }
      if (status) {
        throw new Error(detail || `Search failed with status ${status}.`);
      }
    }
    throw new Error('Unable to search jobs right now.');
  }
}

export async function updateFeedJobStatus(
  token: string,
  jobId: string,
  status: 'saved' | 'dismissed',
): Promise<void> {
  try {
    await httpClient.patch(
      `/jobs/feed/${jobId}`,
      { status },
      { headers: buildAuthHeader(token) },
    );
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const statusCode = error.response?.status;
      const detail = error.response?.data?.detail?.trim();
      if (statusCode === 404) {
        throw new Error('This job is no longer available in your feed.');
      }
      if (statusCode === 401) {
        throw new Error('Session expired. Please sign in again.');
      }
      if (statusCode) {
        throw new Error(detail || `Unable to update job with status ${statusCode}.`);
      }
    }
    throw new Error('Unable to update job status right now.');
  }
}

export async function createJobFromUrl(token: string, payload: CreateJobPayload): Promise<JobItem> {
  try {
    const response = await httpClient.post<JobItem>('/jobs', payload, {
      headers: buildAuthHeader(token),
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
        throw new Error(detail || `Unable to add job URL with status ${status}.`);
      }
    }
    throw new Error('Unable to add job URL right now.');
  }
}
