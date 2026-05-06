import React from 'react';
import { CheckCircle, XCircle, AlertCircle, RefreshCw, Trash2 } from 'lucide-react';

export type BillingEventType =
  | 'checkout_completed'
  | 'invoice_paid'
  | 'payment_failed'
  | 'subscription_updated'
  | 'subscription_canceled'
  | 'subscription_deleted';

export interface BillingEvent {
  id: string;
  type: BillingEventType;
  timestamp: string;
  description: string;
  metadata?: Record<string, any>;
}

export interface BillingEventTimelineProps {
  events: BillingEvent[];
}

const eventConfig: Record<
  BillingEventType,
  { icon: any; color: string; label: string }
> = {
  checkout_completed: {
    icon: CheckCircle,
    color: 'text-success',
    label: 'Checkout Completed',
  },
  invoice_paid: {
    icon: CheckCircle,
    color: 'text-success',
    label: 'Invoice Paid',
  },
  payment_failed: {
    icon: XCircle,
    color: 'text-destructive',
    label: 'Payment Failed',
  },
  subscription_updated: {
    icon: RefreshCw,
    color: 'text-info',
    label: 'Subscription Updated',
  },
  subscription_canceled: {
    icon: AlertCircle,
    color: 'text-warning',
    label: 'Subscription Canceled',
  },
  subscription_deleted: {
    icon: Trash2,
    color: 'text-destructive',
    label: 'Subscription Deleted',
  },
};

export const BillingEventTimeline: React.FC<BillingEventTimelineProps> = ({ events }) => {
  return (
    <div className="space-y-4">
      {events.map((event, index) => {
        const config = eventConfig[event.type];
        const Icon = config.icon;
        const isLast = index === events.length - 1;

        return (
          <div key={event.id} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className={`h-10 w-10 rounded-full bg-card border-2 border-border flex items-center justify-center ${config.color}`}>
                <Icon className="h-5 w-5" />
              </div>
              {!isLast && <div className="flex-1 w-0.5 bg-border mt-2" style={{ minHeight: '2rem' }} />}
            </div>
            <div className="flex-1 pb-8">
              <div className="flex items-start justify-between mb-1">
                <h4 className="font-semibold text-foreground">{config.label}</h4>
                <span className="text-sm text-muted-foreground">
                  {new Date(event.timestamp).toLocaleString()}
                </span>
              </div>
              <p className="text-sm text-muted-foreground mb-2">{event.description}</p>
              {event.metadata && Object.keys(event.metadata).length > 0 && (
                <div className="mt-2 p-3 rounded-lg bg-muted text-xs">
                  <code className="text-foreground">
                    {JSON.stringify(event.metadata, null, 2)}
                  </code>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
