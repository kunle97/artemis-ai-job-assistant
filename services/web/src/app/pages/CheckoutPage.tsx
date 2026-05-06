'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, Button, Input } from '../components/ui';
import { Sparkles, Lock, ArrowLeft, Loader } from 'lucide-react';
import { PlanTier, BillingInterval } from '../components/billing';

export const CheckoutPage: React.FC = () => {
  const router = useRouter();
  const [promoCode, setPromoCode] = useState('');
  const [redirecting, setRedirecting] = useState(false);

  // In a real app, these would come from URL params
  const plan: PlanTier = 'premium';
  const interval = 'monthly' as BillingInterval;
  const price = interval === 'monthly' ? 29 : 24 * 12;

  const handleProceedToStripe = () => {
    setRedirecting(true);
    // In a real app, this would create a Stripe checkout session
    setTimeout(() => {
      router.push('/checkout/success');
    }, 2000);
  };

  const handleGoBack = () => {
    router.back();
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Sparkles className="h-10 w-10 text-brand" />
            <span className="text-3xl font-semibold text-foreground">Artemis</span>
          </div>
          <button
            onClick={handleGoBack}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground mx-auto"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to pricing
          </button>
        </div>

        <Card>
          <div className="p-6 space-y-6">
            <div>
              <h1 className="text-2xl font-semibold text-foreground mb-2">Complete Your Purchase</h1>
              <p className="text-muted-foreground">
                You are about to subscribe to the {plan.charAt(0).toUpperCase() + plan.slice(1)} plan
              </p>
            </div>

            {/* Order Summary */}
            <div className="p-4 rounded-lg bg-secondary/50 border border-border">
              <h3 className="font-semibold text-foreground mb-4">Order Summary</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Plan</span>
                  <span className="font-medium text-foreground">
                    {plan.charAt(0).toUpperCase() + plan.slice(1)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Billing interval</span>
                  <span className="font-medium text-foreground">
                    {interval === 'monthly' ? 'Monthly' : 'Yearly'}
                  </span>
                </div>
                {interval === 'yearly' && (
                  <div className="flex justify-between text-sm">
                    <span className="text-success">Yearly discount</span>
                    <span className="text-success font-medium">-17%</span>
                  </div>
                )}
                <div className="pt-3 border-t border-border flex justify-between">
                  <span className="font-semibold text-foreground">Total</span>
                  <span className="text-2xl font-semibold text-foreground">${price}</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  {interval === 'monthly'
                    ? 'Billed monthly. Cancel anytime.'
                    : `Billed yearly as $${price}. That's $${(price / 12).toFixed(2)}/month.`}
                </p>
              </div>
            </div>

            {/* 14-Day Trial Notice */}
            <div className="p-4 rounded-lg bg-brand/5 border border-brand/20">
              <p className="text-sm text-foreground">
                <strong>14-day free trial included.</strong> You won't be charged until the trial ends. Cancel
                anytime during the trial with no charge.
              </p>
            </div>

            {/* Promo Code */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Promo Code (Optional)</label>
              <Input
                placeholder="Enter promo code"
                value={promoCode}
                onChange={(e) => setPromoCode(e.target.value)}
                fullWidth
              />
            </div>

            {/* Security Notice */}
            <div className="flex items-start gap-3 p-4 rounded-lg bg-muted">
              <Lock className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-foreground mb-1">Secure Checkout</p>
                <p className="text-xs text-muted-foreground">
                  Your payment is processed securely by Stripe. We never store your payment information.
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-3">
              <Button
                variant="primary"
                size="lg"
                fullWidth
                onClick={handleProceedToStripe}
                loading={redirecting}
                disabled={redirecting}
              >
                {redirecting ? (
                  <>
                    <Loader className="h-4 w-4 animate-spin" />
                    Redirecting to secure checkout...
                  </>
                ) : (
                  <>
                    <Lock className="h-4 w-4" />
                    Proceed to Secure Checkout
                  </>
                )}
              </Button>
              <p className="text-xs text-center text-muted-foreground">
                By continuing, you agree to our Terms of Service and Privacy Policy
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
