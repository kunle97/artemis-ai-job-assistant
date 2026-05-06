'use client';
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Input, Card } from '../components/ui';
import { Sparkles, AlertCircle, Loader2 } from 'lucide-react';
import {
  clearStoredTokens,
  getCurrentSession,
  getStoredAccessToken,
  getStoredRefreshToken,
  refreshAccessToken,
  signInUser,
  storeAuthTokens,
} from '../../services/auth/auth.service';

export const SignInPage: React.FC = () => {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionChecking, setSessionChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const runSessionCheck = async () => {
      const params = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
      const reason = params?.get('reason')?.toLowerCase() ?? '';
      if (reason === 'session-expired' || reason === 'expired') {
        setInfoMessage('Your session expired. Please sign in again.');
      }

      const accessToken = getStoredAccessToken();
      if (!accessToken) {
        return;
      }

      setSessionChecking(true);
      setInfoMessage('Already signed in. Redirecting to your dashboard...');

      try {
        await getCurrentSession(accessToken);
        if (!cancelled) {
          router.push('/jobs');
        }
        return;
      } catch {
        const refreshToken = getStoredRefreshToken();
        if (!refreshToken) {
          clearStoredTokens();
          if (!cancelled) {
            setInfoMessage('Your session expired. Please sign in again.');
          }
          return;
        }

        try {
          const refreshed = await refreshAccessToken(refreshToken);
          storeAuthTokens(refreshed);
          await getCurrentSession(refreshed.access_token);
          if (!cancelled) {
            router.push('/jobs');
          }
          return;
        } catch {
          clearStoredTokens();
          if (!cancelled) {
            setInfoMessage('Your session expired. Please sign in again.');
          }
        }
      } finally {
        if (!cancelled) {
          setSessionChecking(false);
        }
      }
    };

    void runSessionCheck();

    return () => {
      cancelled = true;
    };
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const tokens = await signInUser({ email, password });
      storeAuthTokens(tokens);
      router.push('/jobs');
    } catch (authError) {
      const message = authError instanceof Error ? authError.message : 'Sign in failed. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
    }
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
            {infoMessage && (
              <div className="flex items-start gap-3 p-4 rounded-lg bg-brand/10 border border-brand/20">
                <Loader2 className={`h-5 w-5 text-brand flex-shrink-0 mt-0.5 ${sessionChecking ? 'animate-spin' : ''}`} />
                <div className="flex-1">
                  <p className="text-sm text-foreground">{infoMessage}</p>
                </div>
              </div>
            )}

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
              disabled={loading || sessionChecking}
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
              disabled={loading || sessionChecking}
            />

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-border text-brand"
                  disabled={loading || sessionChecking}
                />
                <span className="text-sm text-muted-foreground">Remember me</span>
              </label>
              <button
                type="button"
                onClick={handleForgotPassword}
                className="text-sm text-brand hover:underline"
                disabled={loading || sessionChecking}
              >
                Forgot password?
              </button>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              loading={loading}
              disabled={sessionChecking}
            >
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
            <p className="text-xs text-muted-foreground mt-3">
              We protect your account data and never share your credentials.
            </p>
          </div>
        </Card>

        {/* Back to Home */}
        <div className="mt-6 text-center">
          <button onClick={handleBackToHome} className="text-sm text-muted-foreground hover:text-foreground">
            ← Back to home
          </button>
        </div>
      </div>
    </div>
  );
};
