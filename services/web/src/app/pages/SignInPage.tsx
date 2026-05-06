'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Input, Card } from '../components/ui';
import { Sparkles, AlertCircle } from 'lucide-react';

export const SignInPage: React.FC = () => {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    setTimeout(() => {
      if (email === 'demo@artemis.com' && password === 'demo') {
        router.push('/jobs');
      } else {
        setError('Invalid email or password. Please try again.');
        setLoading(false);
      }
    }, 1000);
  };

  const handleBackToHome = () => {
    router.push('/');
  };

  const handleGoToRegister = () => {
    router.push('/register');
  };

  const handleForgotPassword = () => {
    router.push('/forgot-password');
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Sparkles className="h-10 w-10 text-brand" />
            <span className="text-3xl font-semibold text-foreground">Artemis</span>
          </div>
          <h1 className="text-2xl font-semibold text-foreground">Welcome back</h1>
          <p className="mt-2 text-muted-foreground">Sign in to your account to continue</p>
        </div>

        {/* Sign In Form */}
        <Card>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="flex items-start gap-3 p-4 rounded-lg bg-destructive/10 border border-destructive/20">
                <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-destructive">{error}</p>
                </div>
              </div>
            )}

            <Input
              type="email"
              label="Email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              fullWidth
              autoComplete="email"
            />

            <Input
              type="password"
              label="Password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              fullWidth
              autoComplete="current-password"
            />

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="h-4 w-4 rounded border-border text-brand" />
                <span className="text-sm text-muted-foreground">Remember me</span>
              </label>
              <button type="button" onClick={handleForgotPassword} className="text-sm text-brand hover:underline">
                Forgot password?
              </button>
            </div>

            <Button type="submit" variant="primary" size="lg" fullWidth loading={loading}>
              Sign In
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              Don't have an account?{' '}
              <button onClick={handleGoToRegister} className="text-brand hover:underline font-medium">
                Create one now
              </button>
            </p>
          </div>
        </Card>

        {/* Back to Home */}
        <div className="mt-6 text-center">
          <button onClick={handleBackToHome} className="text-sm text-muted-foreground hover:text-foreground">
            ← Back to home
          </button>
        </div>

        {/* Demo Credentials */}
        <div className="mt-8 p-4 rounded-lg bg-brand-light/20 border border-brand/20">
          <p className="text-sm font-medium text-foreground mb-2">Demo Credentials</p>
          <p className="text-sm text-muted-foreground">
            Email: <code className="px-1 py-0.5 bg-muted rounded">demo@artemis.com</code>
          </p>
          <p className="text-sm text-muted-foreground">
            Password: <code className="px-1 py-0.5 bg-muted rounded">demo</code>
          </p>
        </div>
      </div>
    </div>
  );
};
