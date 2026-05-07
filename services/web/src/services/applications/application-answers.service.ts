/**
 * Application answers service layer for reusable answer library APIs.
 */

import axios from 'axios';
import { httpClient } from '../http/client';
import { redirectToLandingOnSessionExpired } from '../auth/auth.service';

interface ApiErrorBody {
  detail?: string;
}

export interface ApplicationAnswer {
  id: string;
  user_id: string;
  question_key: string;
  category: string | null;
  question_text: string | null;
  answer_text: string;
  created_at: string;
  updated_at: string;
}

export interface ApplicationAnswerCreatePayload {
  question_key: string;
  category?: string | null;
  question_text?: string | null;
  answer_text: string;
}

export interface ApplicationAnswerResolution {
  resolved_answer: string | null;
  source: string;
  needs_review: boolean;
  intent_key: string | null;
}

export function buildApplicationAnswerQuestionKey(questionText: string): string {
  return questionText
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '_')
    .replace(/[^a-z0-9_]/g, '')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 80);
}

function buildAuthHeader(token: string) {
  return {
    Authorization: `Bearer ${token}`,
  };
}

export async function listApplicationAnswers(token: string): Promise<ApplicationAnswer[]> {
  try {
    const response = await httpClient.get<ApplicationAnswer[]>('/application-answers', {
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
        throw new Error(`Failed to load answer library with status ${status}.`);
      }
    }
    throw new Error('Unable to load answer library right now.');
  }
}

export async function saveApplicationAnswer(
  token: string,
  payload: ApplicationAnswerCreatePayload,
): Promise<ApplicationAnswer> {
  try {
    const response = await httpClient.post<ApplicationAnswer>('/application-answers', payload, {
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
        throw new Error(detail || `Failed to save answer with status ${status}.`);
      }
    }
    throw new Error('Unable to save answer right now.');
  }
}

export async function deleteApplicationAnswer(
  token: string,
  answerId: string,
): Promise<void> {
  try {
    await httpClient.delete(`/application-answers/${answerId}`, {
      headers: buildAuthHeader(token),
    });
  } catch (error) {
    if (axios.isAxiosError<ApiErrorBody>(error)) {
      const status = error.response?.status;
      if (status === 401) {
        redirectToLandingOnSessionExpired();
        throw new Error('Session expired. Redirecting to home.');
      }
      if (status === 404) {
        throw new Error('Answer not found.');
      }
      if (status) {
        throw new Error(`Failed to delete answer with status ${status}.`);
      }
    }
    throw new Error('Unable to delete answer right now.');
  }
}

export async function resolveApplicationAnswer(
  token: string,
  questionText: string,
): Promise<ApplicationAnswerResolution> {
  try {
    const response = await httpClient.post<ApplicationAnswerResolution>(
      '/application-answer-resolution',
      { question_text: questionText },
      {
        headers: buildAuthHeader(token),
      },
    );
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
        throw new Error(detail || `Failed to resolve question with status ${status}.`);
      }
    }
    throw new Error('Unable to run answer resolution right now.');
  }
}
