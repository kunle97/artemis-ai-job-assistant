'use client';

/**
 * FollowUpPanel component.
 *
 * Displays the authenticated user's follow-up obligations grouped by
 * urgency (overdue → urgent → upcoming). Fetches from
 * GET /applications/follow-ups on mount; falls back to mock data when
 * no auth token is available.
 *
 * Props:
 *   applicationNames — optional map of application_id → display label so
 *                      items can show a job title instead of a raw UUID.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { AlertCircle, Clock, CalendarDays, RefreshCw, Bell } from 'lucide-react';
import { Card, Badge } from './ui';
import {
  fetchFollowUps,
  MOCK_FOLLOWUPS,
  type FollowUpItem,
  type FollowUpListResponse,
  type FollowUpType,
} from '../../services/applications/followup/followup.service';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const FOLLOWUP_LABELS: Record<FollowUpType, string> = {
  first_followup: 'First follow-up',
  subsequent_followup: 'Follow-up again',
  thank_you: 'Send thank-you',
};

function formatDueDate(iso: string): string {
  const date = new Date(iso);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diff = Math.round((date.getTime() - today.getTime()) / (24 * 60 * 60 * 1000));

  if (diff < 0) return `${Math.abs(diff)}d overdue`;
  if (diff === 0) return 'Due today';
  if (diff === 1) return 'Due tomorrow';
  return `Due in ${diff}d`;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface FollowUpRowProps {
  item: FollowUpItem;
  urgency: 'overdue' | 'urgent' | 'upcoming';
  applicationLabel?: string;
}

const URGENCY_DOT: Record<'overdue' | 'urgent' | 'upcoming', string> = {
  overdue: 'bg-destructive',
  urgent: 'bg-warning',
  upcoming: 'bg-info',
};

const FollowUpRow: React.FC<FollowUpRowProps> = ({ item, urgency, applicationLabel }) => {
  const dotColor = URGENCY_DOT[urgency];
  const label = FOLLOWUP_LABELS[item.followup_type] ?? item.followup_type;
  const dateLabel = formatDueDate(item.due_date);
  const appDisplay = applicationLabel ?? `App #${item.application_id.slice(0, 8)}`;

  return (
    <div className="flex items-center gap-3 py-2.5 px-4 hover:bg-secondary/40 transition-colors rounded-md">
      <span className={`h-2 w-2 rounded-full flex-shrink-0 ${dotColor}`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">{appDisplay}</p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </div>
      <span
        className={`text-xs font-medium flex-shrink-0 ${
          urgency === 'overdue'
            ? 'text-destructive'
            : urgency === 'urgent'
            ? 'text-warning'
            : 'text-muted-foreground'
        }`}
      >
        {dateLabel}
      </span>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface FollowUpPanelProps {
  /**
   * Optional mapping of application_id → display label (e.g. job title +
   * company). When provided, follow-up rows show the application name
   * instead of a truncated UUID.
   */
  applicationNames?: Record<string, string>;
}

export const FollowUpPanel: React.FC<FollowUpPanelProps> = ({ applicationNames = {} }) => {
  const [data, setData] = useState<FollowUpListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token =
        typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

      if (!token) {
        // No auth yet — use mock data so the UI is visible in development
        setData(MOCK_FOLLOWUPS);
        return;
      }

      const result = await fetchFollowUps(token);
      setData(result);
    } catch (err) {
      setError('Could not load follow-ups. Please try again.');
      // Fall back to mock so the panel still renders something useful
      setData(MOCK_FOLLOWUPS);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // -------------------------------------------------------------------------
  // Loading skeleton
  // -------------------------------------------------------------------------
  if (loading) {
    return (
      <Card className="mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Bell className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-semibold text-foreground">Follow-up Reminders</span>
        </div>
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 bg-secondary/50 rounded-md animate-pulse" />
          ))}
        </div>
      </Card>
    );
  }

  // -------------------------------------------------------------------------
  // Empty state — nothing to action
  // -------------------------------------------------------------------------
  if (!data || data.total === 0) {
    return (
      <Card className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Bell className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-semibold text-foreground">Follow-up Reminders</span>
        </div>
        <div className="flex items-center gap-3 py-4 text-muted-foreground">
          <CalendarDays className="h-5 w-5 flex-shrink-0" />
          <p className="text-sm">No follow-ups due right now. Check back after submitting applications.</p>
        </div>
      </Card>
    );
  }

  const overdueCount = data.overdue.length;
  const urgentCount = data.urgent.length;

  return (
    <Card className="mb-6">
      {/* Panel header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-foreground" />
          <span className="text-sm font-semibold text-foreground">Follow-up Reminders</span>
          <Badge variant={overdueCount > 0 ? 'destructive' : urgentCount > 0 ? 'warning' : 'secondary'} size="sm">
            {data.total}
          </Badge>
        </div>
        <button
          onClick={load}
          className="text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Refresh follow-ups"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 mb-3 text-xs text-warning">
          <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="space-y-1">
        {/* Overdue */}
        {data.overdue.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 px-4 py-1.5">
              <AlertCircle className="h-3 w-3 text-destructive" />
              <span className="text-xs font-medium text-destructive uppercase tracking-wide">
                Overdue ({data.overdue.length})
              </span>
            </div>
            {data.overdue.map((item) => (
              <FollowUpRow
                key={item.id}
                item={item}
                urgency="overdue"
                applicationLabel={applicationNames[item.application_id]}
              />
            ))}
          </div>
        )}

        {/* Urgent */}
        {data.urgent.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 px-4 py-1.5">
              <Clock className="h-3 w-3 text-warning" />
              <span className="text-xs font-medium text-warning uppercase tracking-wide">
                Urgent ({data.urgent.length})
              </span>
            </div>
            {data.urgent.map((item) => (
              <FollowUpRow
                key={item.id}
                item={item}
                urgency="urgent"
                applicationLabel={applicationNames[item.application_id]}
              />
            ))}
          </div>
        )}

        {/* Upcoming */}
        {data.upcoming.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 px-4 py-1.5">
              <CalendarDays className="h-3 w-3 text-info" />
              <span className="text-xs font-medium text-info uppercase tracking-wide">
                Upcoming ({data.upcoming.length})
              </span>
            </div>
            {data.upcoming.map((item) => (
              <FollowUpRow
                key={item.id}
                item={item}
                urgency="upcoming"
                applicationLabel={applicationNames[item.application_id]}
              />
            ))}
          </div>
        )}
      </div>
    </Card>
  );
};
