import React from 'react';
import { Button, Card } from '../ui';
import { X, Lock, Sparkles } from 'lucide-react';
import { PlanTier } from './PlanCard';

export interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  requiredPlan: PlanTier;
  featureName: string;
  featureDescription: string;
  benefits: string[];
  onUpgrade: () => void;
}

export const UpgradeModal: React.FC<UpgradeModalProps> = ({
  isOpen,
  onClose,
  requiredPlan,
  featureName,
  featureDescription,
  benefits,
  onUpgrade,
}) => {
  if (!isOpen) return null;

  const planName = requiredPlan.charAt(0).toUpperCase() + requiredPlan.slice(1);

  return (
    <div className="fixed inset-0 bg-foreground/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className="max-w-lg w-full relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-muted-foreground hover:text-foreground"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-12 w-12 rounded-full bg-brand/10 flex items-center justify-center">
              <Lock className="h-6 w-6 text-brand" />
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-foreground">{featureName}</h2>
              <p className="text-sm text-muted-foreground">Requires {planName} plan</p>
            </div>
          </div>

          <p className="text-muted-foreground mb-6">{featureDescription}</p>

          <div className="bg-brand/5 border border-brand/20 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="h-5 w-5 text-brand" />
              <h3 className="font-semibold text-foreground">Unlock with {planName}</h3>
            </div>
            <ul className="space-y-2">
              {benefits.map((benefit, index) => (
                <li key={index} className="text-sm text-foreground flex items-start gap-2">
                  <span className="text-brand mt-0.5">•</span>
                  <span>{benefit}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex gap-3">
            <Button variant="outline" className="w-full" onClick={onClose}>
              Maybe Later
            </Button>
            <Button variant="default" className="w-full" onClick={onUpgrade}>
              Upgrade to {planName}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};
