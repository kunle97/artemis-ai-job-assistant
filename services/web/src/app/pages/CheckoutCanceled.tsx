'use client';
import React from 'react';
import { useRouter } from 'next/navigation';
import { Card, Button } from '../components/ui';
import { Sparkles, XCircle, ArrowLeft, RefreshCw } from 'lucide-react';

export const CheckoutCanceled: React.FC = () => {
  const router = useRouter();

  const handleTryAgain = () => {
    router.push('/#pricing');
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
            <div className="mx-auto h-16 w-16 rounded-full bg-warning/10 flex items-center justify-center">
              <XCircle className="h-10 w-10 text-warning" />
            </div>

            <div>
              <h1 className="text-3xl font-semibold text-foreground mb-2">Checkout Canceled</h1>
              <p className="text-lg text-muted-foreground">
                Your subscription was not completed
              </p>
            </div>

            <div className="p-6 rounded-lg bg-muted text-left">
              <h3 className="font-semibold text-foreground mb-3">What Happened?</h3>
              <p className="text-sm text-muted-foreground mb-4">
                You canceled the checkout process before completing payment. No charges were made to your
                account.
              </p>
              <p className="text-sm text-muted-foreground">
                You can continue using Artemis with your current plan or try upgrading again anytime.
              </p>
            </div>

            <div className="space-y-3">
              <Button variant="primary" size="lg" fullWidth onClick={handleTryAgain}>
                <RefreshCw className="h-4 w-4" />
                Try Again
              </Button>
              <Button variant="outline" size="lg" fullWidth onClick={handleGoToApp}>
                <ArrowLeft className="h-4 w-4" />
                Back to Dashboard
              </Button>
            </div>

            <p className="text-sm text-muted-foreground">
              Need help? Contact our support team at support@artemis.com
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};
