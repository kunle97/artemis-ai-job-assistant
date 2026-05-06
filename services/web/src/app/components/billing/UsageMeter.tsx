import React from 'react';
import { AlertTriangle } from 'lucide-react';

export interface UsageMeterProps {
  label: string;
  current: number;
  limit: number;
  unlimited?: boolean;
  warningThreshold?: number;
}

export const UsageMeter: React.FC<UsageMeterProps> = ({
  label,
  current,
  limit,
  unlimited = false,
  warningThreshold = 0.8,
}) => {
  const percentage = unlimited ? 0 : Math.min((current / limit) * 100, 100);
  const isNearLimit = percentage >= warningThreshold * 100;
  const isAtLimit = current >= limit && !unlimited;

  const getBarColor = () => {
    if (unlimited) return 'bg-brand';
    if (isAtLimit) return 'bg-destructive';
    if (isNearLimit) return 'bg-warning';
    return 'bg-success';
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-foreground">{label}</span>
        <div className="flex items-center gap-2">
          {isNearLimit && !unlimited && (
            <AlertTriangle className="h-4 w-4 text-warning" />
          )}
          <span className="text-sm text-muted-foreground">
            {unlimited ? (
              <span className="font-medium text-brand">Unlimited</span>
            ) : (
              <>
                <span className="font-medium text-foreground">{current.toLocaleString()}</span> /{' '}
                {limit.toLocaleString()}
              </>
            )}
          </span>
        </div>
      </div>

      {!unlimited && (
        <>
          <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${getBarColor()}`}
              style={{ width: `${percentage}%` }}
            />
          </div>

          {isAtLimit && (
            <p className="text-xs text-destructive">Limit reached. Resets monthly or upgrade for more.</p>
          )}

          {isNearLimit && !isAtLimit && (
            <p className="text-xs text-warning">
              {limit - current} remaining. Consider upgrading before you hit the limit.
            </p>
          )}

          {!isNearLimit && (
            <p className="text-xs text-muted-foreground">{limit - current} remaining this month</p>
          )}
        </>
      )}
    </div>
  );
};
