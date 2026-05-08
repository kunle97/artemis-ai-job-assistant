'use client';
import React from 'react';
import { useRouter } from 'next/navigation';
import { Card, Button } from '../components/ui';
import { Sparkles, CheckCircle, ArrowRight } from 'lucide-react';

export const CheckoutSuccess: React.FC = () => {
  const router = useRouter();

  const handleGoToBilling = () => {
    router.push('/account');
  };

  const handleGoToApp = () => {
    router.push('/jobs');
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
        </div>

        <Card>
          <div className="p-8 text-center space-y-6">
            <div className="mx-auto h-16 w-16 rounded-full bg-success/10 flex items-center justify-center">
              <CheckCircle className="h-10 w-10 text-success" />
            </div>

            <div>
              <h1 className="text-3xl font-semibold text-foreground mb-2">Welcome to Premium!</h1>
              <p className="text-lg text-muted-foreground">
                Your subscription has been successfully activated
              </p>
            </div>

            <div className="p-6 rounded-lg bg-brand/5 border border-brand/20 text-left">
              <h3 className="font-semibold text-foreground mb-3">What's Next?</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-brand mt-0.5">•</span>
                  <span>Your 14-day free trial has started. You won't be charged until {new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toLocaleDateString()}</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-brand mt-0.5">•</span>
                  <span>All premium features are now unlocked and ready to use</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-brand mt-0.5">•</span>
                  <span>You can manage your subscription anytime in My Account</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-brand mt-0.5">•</span>
                  <span>Cancel anytime during the trial with no charge</span>
                </li>
              </ul>
            </div>

            <div className="space-y-3">
              <Button variant="primary" size="lg" fullWidth onClick={handleGoToApp}>
                Start Using Premium Features
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="lg" fullWidth onClick={handleGoToBilling}>
                Open My Account
              </Button>
            </div>

            <p className="text-sm text-muted-foreground">
              A confirmation email has been sent to your inbox
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};
