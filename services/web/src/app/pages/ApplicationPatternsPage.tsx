"use client";

/**
 * Application Patterns Dashboard Page.
 *
 * Displays per-user analytics: outcome breakdown, funnel stages,
 * score comparisons, trends over time, and actionable recommendations.
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getApplicationPatterns,
  ApplicationPatternsResponse,
  FunnelEntry,
  TrendPoint,
  Recommendation,
} from "@/services/applications/application-patterns.service";
import { getStoredAccessToken } from "@/services/auth/auth.service";

export function ApplicationPatternsPage() {
  const router = useRouter();

  const [data, setData] = useState<ApplicationPatternsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) {
      router.push("/auth/login");
      return;
    }

    (async () => {
      try {
        setLoading(true);
        const response = await getApplicationPatterns(token);
        setData(response);
        setError(null);
      } catch (err: any) {
        setError(err?.message || "Failed to load patterns");
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-gray-600">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h2 className="text-red-800 font-semibold">Error</h2>
          <p className="text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return <div className="text-center p-8">No data available</div>;
  }

  if (data.total_applications === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 max-w-md">
          <h2 className="text-blue-900 font-semibold mb-2">Get Started</h2>
          <p className="text-blue-800">
            Start applying to jobs to build your analytics dashboard. Once you
            have applications, we'll provide insights into your job search
            patterns.
          </p>
        </div>
      </div>
    );
  }

  if (!data.is_sufficient_data) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 max-w-md">
          <h2 className="text-amber-900 font-semibold mb-2">More Data Needed</h2>
          <p className="text-amber-800 mb-3">
            {data.insufficient_data_message}
          </p>
          <p className="text-sm text-amber-700">
            ({data.total_applications} of {data.minimum_threshold} applications
            needed)
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Application Patterns
        </h1>
        <p className="text-gray-600">
          Your job search analytics • Updated {data.analysis_date}
        </p>
      </div>

      {/* Outcome Summary Cards */}
      {data.outcome_summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <OutcomeSummaryCard
            label="Total"
            value={data.outcome_summary.total}
            color="gray"
          />
          <OutcomeSummaryCard
            label="Positive"
            value={data.outcome_summary.positive}
            color="green"
          />
          <OutcomeSummaryCard
            label="Negative"
            value={data.outcome_summary.negative}
            color="red"
          />
          <OutcomeSummaryCard
            label="Pending"
            value={data.outcome_summary.pending}
            color="blue"
          />
          <OutcomeSummaryCard
            label="Self Filtered"
            value={data.outcome_summary.self_filtered}
            color="yellow"
          />
        </div>
      )}

      {/* Funnel */}
      {data.funnel && data.funnel.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Funnel</h2>
          <div className="space-y-2">
            {data.funnel.map((entry) => (
              <FunnelStage key={entry.status} entry={entry} />
            ))}
          </div>
        </div>
      )}

      {/* Trend */}
      {data.trend && data.trend.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Trend</h2>
          <div className="space-y-2">
            {data.trend.map((point) => (
              <TrendRow key={point.period} point={point} />
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {data.recommendations && data.recommendations.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Recommendations
          </h2>
          <div className="space-y-3">
            {data.recommendations.map((rec, idx) => (
              <RecommendationCard key={idx} recommendation={rec} />
            ))}
          </div>
        </div>
      )}

      {data.recommendations && data.recommendations.length === 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800">
            ✓ Your job search looks healthy! Keep up the momentum.
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * Individual outcome summary card.
 */
function OutcomeSummaryCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: "gray" | "green" | "red" | "blue" | "yellow";
}) {
  const colorClasses = {
    gray: "bg-gray-50 border-gray-200 text-gray-900",
    green: "bg-green-50 border-green-200 text-green-900",
    red: "bg-red-50 border-red-200 text-red-900",
    blue: "bg-blue-50 border-blue-200 text-blue-900",
    yellow: "bg-yellow-50 border-yellow-200 text-yellow-900",
  };

  return (
    <div
      className={`border rounded-lg p-4 text-center ${colorClasses[color]}`}
    >
      <div className="text-sm font-medium opacity-75">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}

/**
 * Funnel stage row.
 */
function FunnelStage({ entry }: { entry: FunnelEntry }) {
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-gray-700 capitalize">
          {entry.status.replace(/_/g, " ")}
        </span>
        <span className="text-sm text-gray-600">
          {entry.count} ({entry.percentage}%)
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-blue-600 h-2 rounded-full"
          style={{ width: `${entry.percentage}%` }}
        />
      </div>
    </div>
  );
}

/**
 * Trend row (period, totals, conversion rate).
 */
function TrendRow({ point }: { point: TrendPoint }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
      <span className="font-medium text-gray-700">{point.period}</span>
      <div className="flex items-center gap-4 text-sm">
        <span className="text-gray-600">
          {point.positive} of {point.total} positive
        </span>
        <span className="font-medium text-gray-900">
          {point.conversion_rate}% conversion
        </span>
      </div>
    </div>
  );
}

/**
 * Recommendation card.
 */
function RecommendationCard({ recommendation }: { recommendation: Recommendation }) {
  const impactColor = {
    high: "bg-red-50 border-red-200 text-red-900",
    medium: "bg-yellow-50 border-yellow-200 text-yellow-900",
    low: "bg-blue-50 border-blue-200 text-blue-900",
  }[recommendation.impact] || "bg-gray-50 border-gray-200 text-gray-900";

  return (
    <div className={`border rounded-lg p-4 ${impactColor}`}>
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold">{recommendation.action}</h3>
        <span className="text-xs font-bold px-2 py-1 bg-white rounded capitalize">
          {recommendation.impact} impact
        </span>
      </div>
      <p className="text-sm opacity-80">{recommendation.reasoning}</p>
    </div>
  );
}
