'use client';

/**
 * FollowUpDropdown component.
 *
 * Bell icon button for the app header. Shows a red badge with the count of
 * overdue/urgent items. Clicking opens a Radix Popover listing follow-ups
 * grouped by urgency (overdue → urgent → upcoming).
 */

import React, { useEffect, useState, useCallback } from 'react';
import { Bell, AlertCircle, Clock, CalendarDays, RefreshCw } from 'lucide-react';
import { Popover, PopoverTrigger, PopoverContent } from './ui/popover';
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
// Single row inside the dropdown
// ---------------------------------------------------------------------------

interface FollowUpRowProps {
  item: FollowUpItem;
  urgency: 'overdue' | 'urgent' | 'upcoming';
  applicationLabel?: string;
}

const DOT: Record<'overdue' | 'urgent' | 'upcoming', string> = {
  overdue: 'bg-destructive',
  urgent: 'bg-warning',
  upcoming: 'bg-info',
};

const DATE_COLOR: Record<'overdue' | 'urgent' | 'upcoming', string> = {
  overdue: 'text-destructive',
  urgent: 'text-warning',
  upcoming: 'text-muted-foreground',
};

const FollowUpRow: React.FC<FollowUpRowProps> = ({ item, urgency, applicationLabel }) => (
  <div className="flex items-center gap-3 py-2 px-3 rounded-md hover:bg-secondary/50 transition-colors">
    <span className={`h-1.5 w-1.5 rounded-full flex-shrink-0 mt-0.5 ${DOT[urgency]}`} />
    <div className="flex-1 min-w-0">
      <p className="text-xs font-medium text-foreground truncate">
        {applicationLabel ?? `App #${item.application_id.slice(0, 8)}`}
      </p>
      <p className="text-[11px] text-muted-foreground">
        {FOLLOWUP_LABELS[item.followup_type] ?? item.followup_type}
      </p>
    </div>
    <span className={`text-[11px] font-medium flex-shrink-0 ${DATE_COLOR[urgency]}`}>
      {formatDueDate(item.due_date)}
    </span>
  </div>
);

// ---------------------------------------------------------------------------
// Section header inside the dropdown
// ---------------------------------------------------------------------------

const SectionHeader: React.FC<{
  icon: React.ElementType;
  label: string;
  count: number;
  colorClass: string;
}> = ({ icon: Icon, label, count, colorClass }) => (
  <div className={`flex items-center gap-1.5 px-3 pt-3 pb-1 ${colorClass}`}>
    <Icon className="h-3 w-3" />
    <span className="text-[10px] font-semibold uppercase tracking-wide">
      {label} ({count})
    </span>
  </div>
);

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface FollowUpDropdownProps {
  applicationNames?: Record<string, string>;
}

export const FollowUpDropdown: React.FC<FollowUpDropdownProps> = ({
  applicationNames = {},
}) => {
  const [data, setData] = useState<FollowUpListResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const token =
        typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      setData(token ? await fetchFollowUps(token) : MOCK_FOLLOWUPS);
    } catch {
      setData(MOCK_FOLLOWUPS);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const overdueCount = data?.overdue.length ?? 0;
  const urgentCount = data?.urgent.length ?? 0;
  const badgeCount = overdueCount + urgentCount;

  return (
    <Popover>
      {/* ── Bell trigger ── */}
      <PopoverTrigger asChild>
        <button
          className="relative flex items-center justify-center h-9 w-9 rounded-full hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground"
          aria-label="Follow-up reminders"
        >
          <Bell className="h-5 w-5" />
          {badgeCount > 0 && (
            <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-destructive" />
          )}
        </button>
      </PopoverTrigger>

      {/* ── Dropdown panel ── */}
      <PopoverContent
        align="end"
        sideOffset={8}
        className="w-80 p-0 overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-foreground" />
            <span className="text-sm font-semibold text-foreground">Follow-ups</span>
            {!loading && data && data.total > 0 && (
              <span className="text-[10px] font-medium bg-secondary text-muted-foreground rounded-full px-1.5 py-0.5">
                {data.total}
              </span>
            )}
          </div>
          <button
            onClick={load}
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Refresh"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Body */}
        <div className="max-h-[420px] overflow-y-auto">
          {loading && (
            <div className="space-y-2 p-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-9 bg-secondary/60 rounded-md animate-pulse" />
              ))}
            </div>
          )}

          {!loading && (!data || data.total === 0) && (
            <div className="flex flex-col items-center justify-center gap-2 py-10 text-muted-foreground">
              <CalendarDays className="h-6 w-6" />
              <p className="text-xs text-center px-4">
                No follow-ups due. Check back after submitting applications.
              </p>
            </div>
          )}

          {!loading && data && data.total > 0 && (
            <div className="pb-2">
              {data.overdue.length > 0 && (
                <>
                  <SectionHeader
                    icon={AlertCircle}
                    label="Overdue"
                    count={data.overdue.length}
                    colorClass="text-destructive"
                  />
                  {data.overdue.map((item) => (
                    <FollowUpRow
                      key={item.id}
                      item={item}
                      urgency="overdue"
                      applicationLabel={applicationNames[item.application_id]}
                    />
                  ))}
                </>
              )}

              {data.urgent.length > 0 && (
                <>
                  <SectionHeader
                    icon={Clock}
                    label="Urgent"
                    count={data.urgent.length}
                    colorClass="text-warning"
                  />
                  {data.urgent.map((item) => (
                    <FollowUpRow
                      key={item.id}
                      item={item}
                      urgency="urgent"
                      applicationLabel={applicationNames[item.application_id]}
                    />
                  ))}
                </>
              )}

              {data.upcoming.length > 0 && (
                <>
                  <SectionHeader
                    icon={CalendarDays}
                    label="Upcoming"
                    count={data.upcoming.length}
                    colorClass="text-info"
                  />
                  {data.upcoming.map((item) => (
                    <FollowUpRow
                      key={item.id}
                      item={item}
                      urgency="upcoming"
                      applicationLabel={applicationNames[item.application_id]}
                    />
                  ))}
                </>
              )}
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
};
