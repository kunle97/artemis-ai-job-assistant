'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '../components/AppShell';
import { Button, Card, CardHeader, CardTitle, CardContent, Badge } from '../components/ui';
import {
  SubscriptionStatusBadge,
  UsageMeter,
  BillingAlertBanner,
  PlanTier,
  SubscriptionStatus,
  BillingInterval,
} from '../components/billing';
import { CreditCard, ExternalLink, TrendingUp, Calendar } from 'lucide-react';

interface BillingHubProps {
  // In a real app, these would come from an API
  currentPlan?: PlanTier;
  status?: SubscriptionStatus;
  interval?: BillingInterval;
  renewalDate?: string;
  usage?: {
    jobScans: { current: number; limit: number; unlimited?: boolean };
    applications: { current: number; limit: number; unlimited?: boolean };
    automationFills: { current: number; limit: number; unlimited?: boolean };
  };
}

export const BillingHub: React.FC<BillingHubProps> = ({
  currentPlan = 'premium',
  status = 'active',
  interval = 'monthly',
  renewalDate = '2026-06-05',
  usage = {
    jobScans: { current: 67, limit: 100 },
    applications: { current: 12, limit: 20 },
    automationFills: { current: 38, limit: 50 },
  },
}) => {
  const [canceling, setCanceling] = useState(false);
  const router = useRouter();

  const handleUpgrade = () => {
    router.push('/checkout?upgrade=true');
  };

  const handleDowngrade = () => {
    router.push('/checkout?downgrade=true');
  };

  const handleManageBilling = () => {
    // In a real app, this would redirect to Stripe customer portal
    window.open('https://billing.stripe.com/p/login/test_abcd1234', '_blank');
  };

  const handleCancelSubscription = () => {
    setCanceling(true);
    setTimeout(() => {
      setCanceling(false);
      alert('Subscription will be canceled at period end');
    }, 1500);
  };

  const planName = currentPlan.charAt(0).toUpperCase() + currentPlan.slice(1);
  const isFree = currentPlan === 'free';
  const isPro = currentPlan === 'pro';

  const getStatusBanner = () => {
    switch (status) {
      case 'past_due':
        return (
          <BillingAlertBanner
            type="error"
            title="Payment Failed"
            message="Your payment method was declined. Please update your payment information to avoid service interruption."
            actionText="Update Payment Method"
            onAction={handleManageBilling}
          />
        );
      case 'canceled':
        return (
          <BillingAlertBanner
            type="warning"
            title="Subscription Canceled"
            message={`Your subscription will end on ${renewalDate}. Reactivate to continue enjoying premium features.`}
            actionText="Reactivate Subscription"
            onAction={handleUpgrade}
          />
        );
      case 'incomplete':
        return (
          <BillingAlertBanner
            type="warning"
            title="Action Required"
            message="Your subscription setup is incomplete. Complete payment to activate your plan."
            actionText="Complete Setup"
            onAction={handleManageBilling}
          />
        );
      case 'trialing':
        return (
          <BillingAlertBanner
            type="info"
            title="Free Trial Active"
            message={`Your trial ends on ${renewalDate}. Add a payment method to continue after the trial.`}
            actionText="Add Payment Method"
            onAction={handleManageBilling}
          />
        );
      default:
        return null;
    }
  };

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-semibold text-foreground">Billing & Subscription</h1>
          <p className="mt-2 text-muted-foreground">Manage your plan, usage, and payment settings</p>
        </div>

        <div className="space-y-6">
          {/* Status Banner */}
          {getStatusBanner()}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Current Plan */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Current Plan</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-2xl font-semibold text-foreground">{planName}</h3>
                      <SubscriptionStatusBadge status={status} />
                    </div>
                    <p className="text-muted-foreground">
                      {interval === 'monthly' ? 'Billed monthly' : 'Billed yearly'}
                    </p>
                  </div>
                  {!isFree && (
                    <div className="text-right">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">
                          {status === 'canceled' ? 'Ends' : 'Renews'} {renewalDate}
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap gap-3">
                  {!isPro && (
                    <Button variant="primary" onClick={handleUpgrade}>
                      <TrendingUp className="h-4 w-4" />
                      {isFree ? 'Upgrade to Premium' : 'Upgrade to Pro'}
                    </Button>
                  )}
                  {!isFree && status !== 'canceled' && (
                    <>
                      <Button variant="outline" onClick={handleManageBilling}>
                        <CreditCard className="h-4 w-4" />
                        Manage Billing
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        onClick={handleCancelSubscription}
                        loading={canceling}
                      >
                        Cancel at Period End
                      </Button>
                    </>
                  )}
                </div>

                {isFree && (
                  <div className="p-4 rounded-lg bg-brand/5 border border-brand/20">
                    <h4 className="font-semibold text-foreground mb-2">Unlock More with Premium</h4>
                    <ul className="space-y-1 text-sm text-muted-foreground">
                      <li>• 10x more job scans per month</li>
                      <li>• 6x more applications per month</li>
                      <li>• 10x more automation fills</li>
                      <li>• Priority support queue</li>
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle>Billing Portal</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Manage payment methods, view invoices, and update billing details securely through Stripe.
                </p>
                <Button variant="outline" fullWidth onClick={handleManageBilling}>
                  <ExternalLink className="h-4 w-4" />
                  Open Billing Portal
                </Button>
                <div className="pt-4 border-t border-border">
                  <p className="text-xs text-muted-foreground">
                    Billing is securely processed by Stripe. Your payment information is never stored on our servers.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Usage Section */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Monthly Usage</CardTitle>
                <span className="text-sm text-muted-foreground">Resets on the 1st of each month</span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <UsageMeter
                  label="Job Scans"
                  current={usage.jobScans.current}
                  limit={usage.jobScans.limit}
                  unlimited={usage.jobScans.unlimited}
                />
                <UsageMeter
                  label="Applications"
                  current={usage.applications.current}
                  limit={usage.applications.limit}
                  unlimited={usage.applications.unlimited}
                />
                <UsageMeter
                  label="Automation Fills"
                  current={usage.automationFills.current}
                  limit={usage.automationFills.limit}
                  unlimited={usage.automationFills.unlimited}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
};
