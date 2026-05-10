/**
 * Application workspace service layer for application detail orchestration APIs.
 */

import axios from 'axios';
import { httpClient } from '../http/client';
import { redirectToLandingOnSessionExpired } from '../auth/auth.service';
import type { JobItem } from '../jobs/job-feed.service';

interface ApiErrorBody {
  detail?: string;
}

export interface ApplicationRecord {
  id: string;
  user_id: string;
  job_id: string;
  resume_id: string | null;
  status: string;
  is_ready_for_automation: boolean;
  is_authorized_to_submit: boolean;
  manual_review_required: boolean;
  notes: string | null;
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationStatusRecord {
  application_id: string;
  status: string;
  is_ready_for_automation: boolean;
  manual_review_required: boolean;
  is_authorized_to_submit: boolean;
  failure_reason: string | null;
  missing_items: string[];
  available_answer_keys: string[];
}

export interface ApplicationReadinessRecord {
  application_id: string;
  is_ready: boolean;
  missing_items: string[];
  available_answer_keys: string[];
}

export interface ApplicationPlanningItemRecord {
  field_key: string;
  question_text: string;
  matched_question_key: string | null;
  resolved_answer: string | null;
  source: string;
  needs_review: boolean;
}

export interface ApplicationPlanningRecord {
  application_id: string;
  readiness_status: 'ready' | 'needs_review';
  missing_items: string[];
  items: ApplicationPlanningItemRecord[];
}

export interface ApplicationRunDispatchRecord {
  application_id: string;
  task_id: string;
  status: string;
}

export interface AutomationInspectedField {
  field_type: string;
  input_subtype: string | null;
  label: string | null;
  name: string | null;
  placeholder: string | null;
  required: boolean;
}

export interface ApplicationPageInspectionRecord {
  application_url: string;
  status: string;
  title: string | null;
  job_context: string | null;
  already_applied: boolean;
  fields: AutomationInspectedField[];
  screenshot_path: string | null;
  notes: string[];
}

export interface AutomationPlannedFieldRecord {
  field_type: string;
  input_subtype: string | null;
  label: string | null;
  name: string | null;
  placeholder: string | null;
  required: boolean;
  options: Array<Record<string, unknown>>;
  classified_role: string;
  resolved_value: string | null;
  needs_review: boolean;
}

export interface AutomationFillPlanRecord {
  application_url: string;
  fields: AutomationPlannedFieldRecord[];
  notes: string[];
}

export interface ApplicationCreatePayload {
  job_id: string;
  resume_id?: string | null;
  notes?: string | null;
}

function buildAuthHeader(token: string) {
  return {
    Authorization: `Bearer ${token}`,
  };
}

function parseApiError(error: unknown, fallback: string): never {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    const status = error.response?.status;
    const detail = error.response?.data?.detail?.trim();
    if (status === 401) {
      redirectToLandingOnSessionExpired();
      throw new Error('Session expired. Redirecting to sign in.');
    }
    if (status) {
      throw new Error(detail || fallback.replace('{status}', String(status)));
    }
  }
  throw new Error(fallback.replace(' with status {status}', ''));
}

export async function getApplicationById(token: string, applicationId: string): Promise<ApplicationRecord> {
  try {
    const response = await httpClient.get<ApplicationRecord>(`/applications/${applicationId}`, {
      headers: buildAuthHeader(token),
    });
    return response.data;
  } catch (error) {
    parseApiError(error, 'Failed to load application with status {status}.');
  }
}

export async function getApplicationStatus(token: string, applicationId: string): Promise<ApplicationStatusRecord> {
  try {
    const response = await httpClient.get<ApplicationStatusRecord>(`/applications/${applicationId}/status`, {
      headers: buildAuthHeader(token),
    });
    return response.data;
  } catch (error) {
    parseApiError(error, 'Failed to load application status with status {status}.');
  }
}

export async function getApplicationReadiness(token: string, applicationId: string): Promise<ApplicationReadinessRecord> {
  try {
    const response = await httpClient.get<ApplicationReadinessRecord>(`/application-readiness/${applicationId}`, {
      headers: buildAuthHeader(token),
    });
    return response.data;
  } catch (error) {
    parseApiError(error, 'Failed to load readiness with status {status}.');
  }
}

export async function buildApplicationPlan(
  token: string,
  applicationId: string,
  questions: string[],
): Promise<ApplicationPlanningRecord> {
  try {
    const response = await httpClient.post<ApplicationPlanningRecord>(
      '/application-planning',
      {
        application_id: applicationId,
        questions,
      },
      {
        headers: buildAuthHeader(token),
      },
    );
    return response.data;
  } catch (error) {
    parseApiError(error, 'Failed to build planning with status {status}.');
  }
}

export async function runApplicationPipeline(
  token: string,
  applicationId: string,
): Promise<ApplicationRunDispatchRecord> {
  try {
    const response = await httpClient.post<ApplicationRunDispatchRecord>(
      `/applications/${applicationId}/run`,
      undefined,
      {
        headers: buildAuthHeader(token),
      },
    );
    return response.data;
  } catch (error) {
    parseApiError(error, 'Failed to run automation with status {status}.');
  }
}

export async function inspectApplicationPage(
  token: string,
  applicationUrl: string,
): Promise<ApplicationPageInspectionRecord> {
  try {
    const response = await httpClient.post<ApplicationPageInspectionRecord>(
      '/automation/inspect',
      {
        application_url: applicationUrl,
      },
      {
        headers: buildAuthHeader(token),
      },
    );
    return response.data;
  } catch (error) {
    parseApiError(error, 'Failed to inspect application page with status {status}.');
  }
}

export async function buildAutomationFillPlan(
  token: string,
  payload: {
    application_url: string;
    inspected_fields: AutomationInspectedField[];
    page_title?: string | null;
    job_context?: string | null;
  },
): Promise<AutomationFillPlanRecord> {
  try {
    const response = await httpClient.post<AutomationFillPlanRecord>(
      '/automation-planning',
      payload,
      {
        headers: buildAuthHeader(token),
      },
    );
    return response.data;
  } catch (error) {
    parseApiError(error, 'Failed to build automation plan with status {status}.');
  }
}

export async function authorizeApplication(token: string, applicationId: string): Promise<ApplicationRecord> {
  try {
    const response = await httpClient.post<ApplicationRecord>(
      `/applications/${applicationId}/authorize`,
      undefined,
      {
        headers: buildAuthHeader(token),
      },
    );
    return response.data;
  } catch (error) {
    parseApiError(error, 'Failed to authorize submission with status {status}.');
  }
}

export async function submitApplication(token: string, applicationId: string): Promise<ApplicationRecord> {
  try {
    const response = await httpClient.post<ApplicationRecord>(
      `/applications/${applicationId}/submit`,
      undefined,
      {
        headers: buildAuthHeader(token),
      },
    );
    return response.data;
  } catch (error) {
    parseApiError(error, 'Failed to submit application with status {status}.');
  }
}

export async function listApplications(token: string): Promise<ApplicationRecord[]> {
  try {
    const response = await httpClient.get<ApplicationRecord[]>('/applications', {
      headers: buildAuthHeader(token),
    });
    return response.data;
  } catch (error) {
    parseApiError(error, 'Failed to load applications with status {status}.');
  }
}

export async function createApplication(
  token: string,
  payload: ApplicationCreatePayload,
): Promise<ApplicationRecord> {
  try {
    const response = await httpClient.post<ApplicationRecord>('/applications', payload, {
      headers: buildAuthHeader(token),
    });
    return response.data;
  } catch (error) {
    parseApiError(error, 'Failed to create application with status {status}.');
  }
}

export async function getJobById(token: string, jobId: string): Promise<JobItem | null> {
  try {
    const response = await httpClient.get<JobItem>(`/jobs/${jobId}`, {
      headers: buildAuthHeader(token),
    });
    return response.data;
  } catch {
    return null;
  }
}
