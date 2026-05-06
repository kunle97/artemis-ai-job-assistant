import React from 'react';
import { Button } from '../ui';
import { AlertCircle, AlertTriangle, Info, CheckCircle } from 'lucide-react';

export type AlertType = 'error' | 'warning' | 'info' | 'success';

export interface BillingAlertBannerProps {
  type: AlertType;
  title: string;
  message: string;
  actionText?: string;
  onAction?: () => void;
}

const alertConfig: Record<
  AlertType,
  { icon: any; bgColor: string; borderColor: string; iconColor: string }
> = {
  error: {
    icon: AlertCircle,
    bgColor: 'bg-destructive/10',
    borderColor: 'border-destructive/20',
    iconColor: 'text-destructive',
  },
  warning: {
    icon: AlertTriangle,
    bgColor: 'bg-warning/10',
    borderColor: 'border-warning/20',
    iconColor: 'text-warning',
  },
  info: {
    icon: Info,
    bgColor: 'bg-info/10',
    borderColor: 'border-info/20',
    iconColor: 'text-info',
  },
  success: {
    icon: CheckCircle,
    bgColor: 'bg-success/10',
    borderColor: 'border-success/20',
    iconColor: 'text-success',
  },
};

export const BillingAlertBanner: React.FC<BillingAlertBannerProps> = ({
  type,
  title,
  message,
  actionText,
  onAction,
}) => {
  const config = alertConfig[type];
  const Icon = config.icon;

  return (
    <div className={`rounded-lg border p-4 ${config.bgColor} ${config.borderColor}`}>
      <div className="flex items-start gap-3">
        <Icon className={`h-5 w-5 flex-shrink-0 mt-0.5 ${config.iconColor}`} />
        <div className="flex-1">
          <h4 className="font-semibold text-foreground mb-1">{title}</h4>
          <p className="text-sm text-muted-foreground">{message}</p>
          {actionText && onAction && (
            <div className="mt-3">
              <Button
                variant={type === 'error' ? 'destructive' : 'default'}
                size="sm"
                onClick={onAction}
              >
                {actionText}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
