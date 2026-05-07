'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { AppShell } from '../components/AppShell';
import { Button, Card, CardContent, CardHeader, CardTitle } from '../components/ui';
import {
  BillingAlertBanner,
  SubscriptionStatusBadge,
  UsageMeter,
  type BillingInterval,
  type PlanTier,
  type SubscriptionStatus,
} from '../components/billing';
import { AlertTriangle, Calendar, CheckCircle, CreditCard, ExternalLink, TrendingUp } from 'lucide-react';
import { getStoredAccessToken } from '../../services/auth/auth.service';
import { getProfile, updateProfile } from '../../services/profile/profile.service';

const UNSAVED_ACCOUNT_TOAST_ID = 'unsaved-account-toast';

export const MyAccountPage: React.FC = () => {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [autoSubmit, setAutoSubmit] = useState(false);
  const [loadingAutoSubmit, setLoadingAutoSubmit] = useState(true);
  const [currentPlan] = useState<PlanTier>('premium');
  const [status] = useState<SubscriptionStatus>('active');
  const [interval] = useState<BillingInterval>('monthly');

  const renewalDate = '2026-06-05';
  const usage = {
    jobScans: { current: 67, limit: 100 },
    applications: { current: 12, limit: 20 },
    automationFills: { current: 38, limit: 50 },
  };

  const handleManageBilling = () => {
    window.open('https://billing.stripe.com/p/login/test_abcd1234', '_blank');
  };

  const handleUpgrade = () => {
    router.push('/checkout?upgrade=true');
  };

  const handleCancelSubscription = () => {
    window.alert('Subscription will be canceled at period end');
  };

  const markUnsavedChanges = () => {
    setHasUnsavedChanges(true);
  };

  const handleSave = () => {
    const token = getStoredAccessToken();
    if (!token) return;

    setSaving(true);
    setSaved(false);
    toast.dismiss(UNSAVED_ACCOUNT_TOAST_ID);

    void updateProfile(token, { auto_submit: autoSubmit })
      .then(() => {
        setSaving(false);
        setSaved(true);
        setHasUnsavedChanges(false);
        setTimeout(() => setSaved(false), 3000);
      })
      .catch(() => {
        setSaving(false);
      });
  };

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) {
      setLoadingAutoSubmit(false);
      return;
    }

    void getProfile(token)
      .then((profile) => {
        setAutoSubmit(profile.auto_submit ?? false);
      })
      .finally(() => {
        setLoadingAutoSubmit(false);
      });
  }, []);

  useEffect(() => {
    if (!hasUnsavedChanges) {
      toast.dismiss(UNSAVED_ACCOUNT_TOAST_ID);
      return;
    }

    toast('Unsaved Changes', {
      id: UNSAVED_ACCOUNT_TOAST_ID,
      duration: Infinity,
      position: 'bottom-center',
      description: 'Save your account settings to apply updates.',
      actionButtonStyle: {
        background: 'var(--brand)',
        color: 'var(--brand-foreground)',
        border: '1px solid var(--brand)',
      },
      action: {
        label: 'Save',
        onClick: handleSave,
      },
    });
  }, [hasUnsavedChanges]);

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

  const planName = currentPlan.charAt(0).toUpperCase() + currentPlan.slice(1);
  const isFree = currentPlan === 'free';
  const isPro = currentPlan === 'pro';

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto">
        <div className="mb-8 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold text-foreground">My Account</h1>
            <p className="mt-2 text-muted-foreground">Manage billing, subscription, and automation settings</p>
          </div>
          {saved && (
            <div className="flex items-center gap-2 text-success">
              <CheckCircle className="h-5 w-5" />
              <span className="font-medium">Account settings saved</span>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <section className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-foreground">Billing & Subscription</h2>
            </div>
            <div className="space-y-6">
              {getStatusBanner()}

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
                          <Button variant="ghost" onClick={handleCancelSubscription}>
                            Cancel at Period End
                          </Button>
                        </>
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Billing Portal</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-muted-foreground">
                      Manage payment methods, invoices, and billing details securely through Stripe.
                    </p>
                    <Button variant="outline" fullWidth onClick={handleManageBilling}>
                      <ExternalLink className="h-4 w-4" />
                      Open Billing Portal
                    </Button>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Monthly Usage</CardTitle>
                    <span className="text-sm text-muted-foreground">Resets on the 1st of each month</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <UsageMeter label="Job Scans" current={usage.jobScans.current} limit={usage.jobScans.limit} />
                    <UsageMeter label="Applications" current={usage.applications.current} limit={usage.applications.limit} />
                    <UsageMeter label="Automation Fills" current={usage.automationFills.current} limit={usage.automationFills.limit} />
                  </div>
                </CardContent>
              </Card>
            </div>
          </section>

          <Card>
            <CardHeader>
              <CardTitle>Automation</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start justify-between gap-4 p-4 rounded-lg border border-destructive/40 bg-destructive/5">
                <div>
                  <p className="font-medium text-foreground">Auto-submit applications</p>
                  <p className="text-sm text-muted-foreground mt-0.5">
                    Submit applications without manual review.
                  </p>
                  <p className="text-xs text-destructive mt-2 inline-flex items-center gap-1">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    High-impact setting: enable with caution.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoSubmit}
                    onChange={(e) => {
                      setAutoSubmit(e.target.checked);
                      markUnsavedChanges();
                    }}
                    disabled={loadingAutoSubmit}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-switch-background peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-ring rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand"></div>
                </label>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
};
