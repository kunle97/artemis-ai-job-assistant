/**
 * Application patterns analysis service.
 *
 * Fetches analytics and pattern data from the backend's patterns endpoint.
 */

import { httpClient } from "../http/client";

export interface OutcomeSummary {
  total: number;
  positive: number;
  negative: number;
  self_filtered: number;
  pending: number;
}

export interface ScoreStats {
  avg: number;
  min: number;
  max: number;
  count: number;
}

export interface ScoreByOutcome {
  positive: ScoreStats;
  negative: ScoreStats;
  self_filtered: ScoreStats;
  pending: ScoreStats;
}

export interface FunnelEntry {
  status: string;
  count: number;
  percentage: number;
}

export interface TrendPoint {
  period: string;
  total: number;
  positive: number;
  conversion_rate: number;
}

export interface Recommendation {
  action: string;
  reasoning: string;
  impact: string;
}

export interface ApplicationPatternsResponse {
  analysis_date: string;
  total_applications: number;
  is_sufficient_data: boolean;
  minimum_threshold: number;
  insufficient_data_message: string | null;
  outcome_summary: OutcomeSummary | null;
  funnel: FunnelEntry[] | null;
  score_by_outcome: ScoreByOutcome | null;
  trend: TrendPoint[] | null;
  recommendations: Recommendation[] | null;
}

/**
 * Fetch application pattern analytics for the authenticated user.
 */
export async function getApplicationPatterns(
  token: string
): Promise<ApplicationPatternsResponse> {
  const response = await httpClient.get<ApplicationPatternsResponse>(
    "/applications/patterns",
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );
  return response.data;
}
