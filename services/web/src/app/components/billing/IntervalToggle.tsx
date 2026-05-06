import React from 'react';
import { BillingInterval } from './PlanCard';

export interface IntervalToggleProps {
  interval: BillingInterval;
  onChange: (interval: BillingInterval) => void;
  yearlyDiscount?: number;
}

export const IntervalToggle: React.FC<IntervalToggleProps> = ({
  interval,
  onChange,
  yearlyDiscount,
}) => {
  return (
    <div className="flex items-center justify-center gap-3">
      <button
        onClick={() => onChange('monthly')}
        className={`px-4 py-2 rounded-lg font-medium transition-colors ${
          interval === 'monthly'
            ? 'bg-brand text-brand-foreground'
            : 'bg-transparent text-muted-foreground hover:text-foreground'
        }`}
      >
        Monthly
      </button>
      <button
        onClick={() => onChange('yearly')}
        className={`px-4 py-2 rounded-lg font-medium transition-colors ${
          interval === 'yearly'
            ? 'bg-brand text-brand-foreground'
            : 'bg-transparent text-muted-foreground hover:text-foreground'
        }`}
      >
        Yearly
        {yearlyDiscount && (
          <span className="ml-2 text-xs bg-success text-success-foreground px-2 py-0.5 rounded-full">
            Save {yearlyDiscount}%
          </span>
        )}
      </button>
    </div>
  );
};
