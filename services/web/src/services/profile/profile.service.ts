/**
 * Profile service layer for candidate profile API calls.
 */

import axios from 'axios';
import { httpClient } from '../http/client';

export interface CandidateExperienceSection {
  id?: string | null;
  role?: string | null;
  position?: string | null;
  company?: string | null;
  start_month?: string | null;
  start_year?: string | null;
  end_month?: string | null;
  end_year?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  currently_working?: boolean | null;
  location?: string | null;
  details?: string[] | null;
}

export interface CandidateProfile {
  id: string;
  user_id: string;
  phone: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  zip_code: string | null;
  salary_target: string | null;
  min_salary: string | null;
  gender: string | null;
  race: string | null;
  veteran_status: string | null;
  disability_status: string | null;
  pronouns: string | null;
  autofill_gender: boolean;
  autofill_race: boolean;
  autofill_veteran_status: boolean;
  autofill_disability_status: boolean;
  autofill_pronouns: boolean;
  auto_submit: boolean;
  current_company: string | null;
  preferred_relocation_cities: string[] | null;
  work_arrangement: string[] | null;
  skills: string[] | null;
  experience_sections: CandidateExperienceSection[] | null;
  location: string | null;
}

export interface CandidateProfileUpdateRequest {
  phone?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  portfolio_url?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  zip_code?: string | null;
  salary_target?: string | null;
  min_salary?: string | null;
  gender?: string | null;
  race?: string | null;
  veteran_status?: string | null;
  disability_status?: string | null;
  pronouns?: string | null;
  autofill_gender?: boolean | null;
  autofill_race?: boolean | null;
  autofill_veteran_status?: boolean | null;
  autofill_disability_status?: boolean | null;
  autofill_pronouns?: boolean | null;
  auto_submit?: boolean | null;
  current_company?: string | null;
  preferred_relocation_cities?: string[] | null;
  work_arrangement?: string[] | null;
  skills?: string[] | null;
  experience_sections?: CandidateExperienceSection[] | null;
}

interface ApiErrorBody {
  detail?: string;
}

export async function getProfile(accessToken: string): Promise<CandidateProfile> {
  try {
    const response = await httpClient.get<CandidateProfile>('/profile', {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail?.trim();
      if (status === 401) throw new Error('Not authenticated. Please sign in again.');
      if (status) throw new Error(detail || `Failed to load profile (status ${status}).`);
    }
    throw new Error('Unable to connect to the server. Please try again.');
  }
}

export async function updateProfile(
  accessToken: string,
  payload: CandidateProfileUpdateRequest,
): Promise<CandidateProfile> {
  try {
    const response = await httpClient.put<CandidateProfile>('/profile', payload, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail?.trim();
      if (status === 401) throw new Error('Not authenticated. Please sign in again.');
      if (status === 422) throw new Error('Some fields have invalid values. Please review and try again.');
      if (status) throw new Error(detail || `Failed to save profile (status ${status}).`);
    }
    throw new Error('Unable to connect to the server. Please try again.');
  }
}
