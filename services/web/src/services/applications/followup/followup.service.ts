/**
 * Follow-up domain service for fetching follow-up notifications from the API.
 */

import { httpClient } from '../../http/client';

export type FollowUpType = 'first_followup' | 'subsequent_followup' | 'thank_you';

export interface FollowUpItem {
  id: string;
  application_id: string;
  user_id: string;
  due_date: string;
  followup_type: FollowUpType;
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
}

export interface FollowUpListResponse {
  overdue: FollowUpItem[];
  urgent: FollowUpItem[];
  upcoming: FollowUpItem[];
  total: number;
}

export async function fetchFollowUps(token: string): Promise<FollowUpListResponse> {
  const response = await httpClient.get<FollowUpListResponse>('/applications/follow-ups', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return response.data;
}

// Mock data used when auth token is not present (demo/dev mode).
const now = new Date();

const daysFromNow = (n: number) =>
  new Date(now.getTime() + n * 24 * 60 * 60 * 1000).toISOString();

export const MOCK_FOLLOWUPS: FollowUpListResponse = {
  overdue: [
    {
      id: 'fu-1',
      application_id: '4',
      user_id: 'user-1',
      due_date: daysFromNow(-3),
      followup_type: 'first_followup',
      is_overdue: true,
      created_at: daysFromNow(-10),
      updated_at: daysFromNow(-3),
    },
  ],
  urgent: [
    {
      id: 'fu-2',
      application_id: '1',
      user_id: 'user-1',
      due_date: daysFromNow(1),
      followup_type: 'subsequent_followup',
      is_overdue: false,
      created_at: daysFromNow(-7),
      updated_at: daysFromNow(-1),
    },
  ],
  upcoming: [
    {
      id: 'fu-3',
      application_id: '3',
      user_id: 'user-1',
      due_date: daysFromNow(5),
      followup_type: 'thank_you',
      is_overdue: false,
      created_at: daysFromNow(-2),
      updated_at: daysFromNow(-1),
    },
    {
      id: 'fu-4',
      application_id: '2',
      user_id: 'user-1',
      due_date: daysFromNow(8),
      followup_type: 'first_followup',
      is_overdue: false,
      created_at: daysFromNow(-5),
      updated_at: daysFromNow(-1),
    },
  ],
  total: 4,
};
