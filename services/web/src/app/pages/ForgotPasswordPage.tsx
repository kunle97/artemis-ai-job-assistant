'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Input, Card, CardHeader, CardTitle, CardContent } from '../components/ui';
import { Sparkles, ArrowLeft, Mail } from 'lucide-react';

export const ForgotPasswordPage: React.FC = () => {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    // Simulate API call
    setTimeout(() => {
      setLoading(false);
      setSubmitted(true);
    }, 1500);
  };

  const handleBackToSignIn = () => {
    router.push('/signin');
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto max-w-7xl px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-8 w-8 text-brand" />
              <span className="text-2xl font-semibold text-foreground">Artemis</span>
            </div>
            <Button variant="ghost" onClick={handleBackToSignIn}>
              <ArrowLeft className="h-4 w-4" />
              Back to Sign In
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          {!submitted ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-center mb-4">
                  <div className="h-12 w-12 rounded-full bg-brand/10 flex items-center justify-center">
                    <Mail className="h-6 w-6 text-brand" />
                  </div>
                </div>
                <CardTitle className="text-center">Forgot Password?</CardTitle>
                <p className="text-center text-sm text-muted-foreground mt-2">
                  No worries! Enter your email and we'll send you reset instructions.
                </p>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <Input
                    label="Email"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    fullWidth
                  />

                  <Button type="submit" variant="primary" fullWidth loading={loading}>
                    Send Reset Link
                  </Button>

                  <Button
                    type="button"
                    variant="ghost"
                    fullWidth
                    onClick={handleBackToSignIn}
                  >
                    <ArrowLeft className="h-4 w-4" />
                    Back to Sign In
                  </Button>
                </form>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-center mb-4">
                  <div className="h-12 w-12 rounded-full bg-success/10 flex items-center justify-center">
                    <Mail className="h-6 w-6 text-success" />
                  </div>
                </div>
                <CardTitle className="text-center">Check Your Email</CardTitle>
                <p className="text-center text-sm text-muted-foreground mt-2">
                  We've sent password reset instructions to <strong>{email}</strong>
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-muted/50">
                  <p className="text-sm text-muted-foreground">
                    Didn't receive the email? Check your spam folder or try again with a different email address.
                  </p>
                </div>

                <Button variant="primary" fullWidth onClick={handleBackToSignIn}>
                  Back to Sign In
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
