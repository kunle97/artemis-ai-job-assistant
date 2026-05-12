/**
 * Resume service layer for uploading resumes and reading parsed metadata.
 */

import axios from 'axios';
import { httpClient } from '../http/client';
import { redirectToLandingOnSessionExpired } from '../auth/auth.service';

interface ApiErrorBody {
  detail?: string;
}

export interface ParsedExperienceEntry {
  company?: string;
  position?: string;
  location?: string;
  start_date?: string;
  end_date?: string;
}

export interface ResumeNormalizedData {
  headline_title?: string | null;
  current_job_title?: string | null;
  current_company?: string | null;
  skills?: string[];
  years_experience?: number | null;
  experience_sections?: ParsedExperienceEntry[];
}

export interface ResumeParsedJson {
  status?: string;
  file_name?: string;
  file_extension?: string;
  character_count?: number;
  normalized_data?: ResumeNormalizedData | null;
}

export interface ResumeUploadResponse {
  id: string;
  user_id: string;
  file_name: string;
  file_path: string;
  mime_type?: string | null;
  extracted_text?: string | null;
  parsed_json?: ResumeParsedJson | null;
  variant_type: string;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
  missing_profile_fields: string[];
  message: string;
}

export interface ResumeRead {
  id: string;
  user_id: string;
  file_name: string;
  file_path: string;
  mime_type?: string | null;
  extracted_text?: string | null;
  parsed_json?: ResumeParsedJson | null;
  variant_type: string;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export async function getResumes(token: string): Promise<ResumeRead[]> {
  try {
    const response = await httpClient.get<ResumeRead[]>('/resumes', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return response.data;
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail?.trim();

      if (status === 401) {
        redirectToLandingOnSessionExpired();
        throw new Error('Session expired. Redirecting to sign in.');
      }

      if (status) {
        throw new Error(detail || `Unable to load resumes (status ${status}).`);
      }
    }

    throw new Error('Unable to load resumes right now. Please try again.');
  }
}

export async function uploadResume(file: File, token: string): Promise<ResumeUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await httpClient.post<ResumeUploadResponse>('/resumes/upload', formData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail?.trim();

      if (status === 401) {
        redirectToLandingOnSessionExpired();
        throw new Error('Session expired. Redirecting to sign in.');
      }

      if (status === 400) {
        throw new Error(detail || 'Resume upload failed. Please use PDF, DOCX, or TXT.');
      }

      if (status) {
        throw new Error(detail || `Resume upload failed with status ${status}.`);
      }
    }

    throw new Error('Unable to upload resume right now. Please try again.');
  }
}

export async function deleteResume(resumeId: string, token: string): Promise<void> {
  try {
    await httpClient.delete(`/resumes/${resumeId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail?.trim();

      if (status === 401) {
        redirectToLandingOnSessionExpired();
        throw new Error('Session expired. Redirecting to sign in.');
      }

      if (status === 404) {
        throw new Error(detail || 'Resume not found.');
      }

      if (status) {
        throw new Error(detail || `Unable to delete resume (status ${status}).`);
      }
    }

    throw new Error('Unable to delete resume right now. Please try again.');
  }
}

export async function setPrimaryResume(resumeId: string, token: string): Promise<ResumeRead> {
  try {
    const response = await httpClient.patch<ResumeRead>(`/resumes/${resumeId}/primary`, undefined, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return response.data;
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail?.trim();

      if (status === 401) {
        redirectToLandingOnSessionExpired();
        throw new Error('Session expired. Redirecting to sign in.');
      }

      if (status === 404) {
        throw new Error(detail || 'Resume not found.');
      }

      if (status) {
        throw new Error(detail || `Unable to update default resume (status ${status}).`);
      }
    }

    throw new Error('Unable to update the default resume right now. Please try again.');
  }
}
