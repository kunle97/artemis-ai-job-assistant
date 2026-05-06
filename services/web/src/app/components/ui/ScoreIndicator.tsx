'use client';

/**
 * ScoreIndicator component.
 *
 * Displays a job fit score (0–5) as a coloured pill with a label derived
 * from the career-ops recommendation tier. Accepts an optional score and
 * recommendation string; renders a neutral placeholder when not yet scored.
 *
 * TODO: wire `score` and `recommendation` props from POST /applications/{id}/score
 * response once the score endpoint is connected to the frontend data layer.
 */

import React from 'react';
import { Sparkles } from 'lucide-react';
import { cn } from './utils';

export type ScoreRecommendation =
  | 'apply_immediately'
  | 'worth_applying'
  | 'apply_if_specific_reason'
  | 'recommend_against'
  | null
  | undefined;

interface ScoreIndicatorProps {
  score?: number | null;
  recommendation?: ScoreRecommendation;
  /** Compact pill mode — used in table rows */
  compact?: boolean;
  className?: string;
}

const RECOMMENDATION_CONFIG: Record<
  NonNullable<ScoreRecommendation>,
  { label: string; color: string; bg: string; border: string }
> = {
  apply_immediately: {
    label: 'Strong Fit',
    color: 'text-success',
    bg: 'bg-success/10',
    border: 'border-success/30',
  },
  worth_applying: {
    label: 'Good Fit',
    color: 'text-info',
    bg: 'bg-info/10',
    border: 'border-info/30',
  },
  apply_if_specific_reason: {
    label: 'Decent Fit',
    color: 'text-warning',
    bg: 'bg-warning/10',
    border: 'border-warning/30',
  },
  recommend_against: {
    label: 'Poor Fit',
    color: 'text-destructive',
    bg: 'bg-destructive/10',
    border: 'border-destructive/30',
  },
};

export const ScoreIndicator: React.FC<ScoreIndicatorProps> = ({
  score,
  recommendation,
  compact = false,
  className,
}) => {
  const config = recommendation ? RECOMMENDATION_CONFIG[recommendation] : null;

  if (compact) {
    // Pill mode for table rows
    if (!config || score == null) {
      return (
        <span className={cn('inline-flex items-center gap-1 text-xs text-muted-foreground', className)}>
          <Sparkles className="h-3 w-3" />
          Not scored
        </span>
      );
    }
    return (
      <span
        className={cn(
          'inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-md border',
          config.bg,
          config.color,
          config.border,
          className,
        )}
      >
        <Sparkles className="h-3 w-3" />
        {score.toFixed(1)} · {config.label}
      </span>
    );
  }

  // Full card mode for detail sidebar
  if (!config || score == null) {
    return (
      <div className={cn('rounded-lg border border-dashed border-border p-4 text-center', className)}>
        <Sparkles className="h-6 w-6 text-muted-foreground mx-auto mb-2" />
        <p className="text-sm font-medium text-muted-foreground">Not yet scored</p>
        <p className="text-xs text-muted-foreground mt-1">
          Run a score to see how well this role matches your profile.
        </p>
      </div>
    );
  }

  const pct = Math.round((score / 5) * 100);

  return (
    <div className={cn('rounded-lg border p-4', config.bg, config.border, className)}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Sparkles className={cn('h-4 w-4', config.color)} />
          <span className={cn('text-sm font-semibold', config.color)}>{config.label}</span>
        </div>
        <span className={cn('text-lg font-bold', config.color)}>{score.toFixed(1)}<span className="text-xs font-normal text-muted-foreground">/5</span></span>
      </div>
      {/* Mini progress bar */}
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all', {
            'bg-success': recommendation === 'apply_immediately',
            'bg-info': recommendation === 'worth_applying',
            'bg-warning': recommendation === 'apply_if_specific_reason',
            'bg-destructive': recommendation === 'recommend_against',
          })}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
};
