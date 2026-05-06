import React from 'react';
import { Button } from '../ui';
import { Check } from 'lucide-react';

export type PlanTier = 'free' | 'premium' | 'pro';
export type BillingInterval = 'monthly' | 'yearly';

interface PlanFeature {
  text: string;
  included: boolean;
}

export interface PlanCardProps {
  tier: PlanTier;
  name: string;
  priceMonthly: number;
  priceYearly: number;
  interval: BillingInterval;
  features: PlanFeature[];
  popular?: boolean;
  currentPlan?: boolean;
  onSelect: () => void;
  ctaText?: string;
}

export const PlanCard: React.FC<PlanCardProps> = ({
  tier,
  name,
  priceMonthly,
  priceYearly,
  interval,
  features,
  popular = false,
  currentPlan = false,
  onSelect,
  ctaText,
}) => {
  const price = interval === 'monthly' ? priceMonthly : priceYearly;
  const yearlyDiscount = priceMonthly > 0 ? Math.round((1 - priceYearly / 12 / priceMonthly) * 100) : 0;

  const getDefaultCTA = () => {
    if (currentPlan) return 'Current Plan';
    if (tier === 'free') return 'Get Started';
    if (tier === 'premium') return 'Upgrade to Premium';
    if (tier === 'pro') return 'Go Pro';
    return 'Select Plan';
  };

  return (
    <div
      className={`relative flex flex-col rounded-lg border-2 bg-card p-6 ${
        popular ? 'border-brand shadow-lg scale-105' : 'border-border'
      } ${currentPlan ? 'ring-2 ring-brand' : ''}`}
    >
      {popular && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2">
          <span className="inline-flex items-center rounded-full bg-brand px-4 py-1 text-sm font-semibold text-brand-foreground">
            Most Popular
          </span>
        </div>
      )}

      {currentPlan && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2">
          <span className="inline-flex items-center rounded-full bg-success px-4 py-1 text-sm font-semibold text-success-foreground">
            Current Plan
          </span>
        </div>
      )}

      <div className="mb-6">
        <h3 className="text-2xl font-semibold text-foreground">{name}</h3>
        <div className="mt-4 flex items-baseline gap-2">
          <span className="text-4xl font-semibold text-foreground">
            ${price === 0 ? '0' : price.toLocaleString()}
          </span>
          {price > 0 && (
            <span className="text-muted-foreground">
              /{interval === 'monthly' ? 'month' : 'year'}
            </span>
          )}
        </div>
        {interval === 'yearly' && yearlyDiscount > 0 && (
          <p className="mt-2 text-sm text-success font-medium">Save {yearlyDiscount}% with yearly billing</p>
        )}
      </div>

      <Button
        variant={popular || tier === 'premium' ? 'default' : currentPlan ? 'secondary' : 'outline'}
        onClick={onSelect}
        disabled={currentPlan}
        className="mb-6 w-full"
      >
        {ctaText || getDefaultCTA()}
      </Button>

      <div className="space-y-3 flex-1">
        {features.map((feature, index) => (
          <div key={index} className="flex items-start gap-3">
            <Check
              className={`h-5 w-5 flex-shrink-0 ${
                feature.included ? 'text-success' : 'text-muted-foreground opacity-30'
              }`}
            />
            <span
              className={`text-sm ${
                feature.included ? 'text-foreground' : 'text-muted-foreground line-through'
              }`}
            >
              {feature.text}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
