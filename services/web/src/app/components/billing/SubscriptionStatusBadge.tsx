import React from 'react';
import { Badge } from '../ui';

export type SubscriptionStatus = 'active' | 'trialing' | 'past_due' | 'canceled' | 'incomplete';

export interface SubscriptionStatusBadgeProps {
  status: SubscriptionStatus;
  size?: 'sm' | 'md' | 'lg';
}

const statusConfig: Record<
  SubscriptionStatus,
  { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }
> = {
  active: { label: 'Active', variant: 'default' },
  trialing: { label: 'Trial', variant: 'secondary' },
  past_due: { label: 'Past Due', variant: 'destructive' },
  canceled: { label: 'Canceled', variant: 'outline' },
  incomplete: { label: 'Incomplete', variant: 'outline' },
};

export const SubscriptionStatusBadge: React.FC<SubscriptionStatusBadgeProps> = ({
  status,
  size = 'md',
}) => {
  const config = statusConfig[status];
  const sizeClass = size === 'sm' ? 'text-[10px]' : size === 'lg' ? 'text-sm px-2.5 py-1' : 'text-xs';

  return (
    <Badge variant={config.variant} className={sizeClass}>
      {config.label}
    </Badge>
  );
};
