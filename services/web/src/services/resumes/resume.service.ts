/**
 * Resume service layer for uploading resumes and reading parsed metadata.
 */

import axios from 'axios';
import { httpClient } from '../http/client';

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
        throw new Error('Your session expired. Please sign in again to upload your resume.');
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
