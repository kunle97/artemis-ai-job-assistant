'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Input, Card, CardHeader, CardTitle, CardContent } from '../components/ui';
import { Sparkles, CheckCircle, Lock } from 'lucide-react';

export const ResetPasswordPage: React.FC = () => {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    // Simulate API call
    setTimeout(() => {
      setLoading(false);
      setSubmitted(true);
    }, 1500);
  };

  const handleGoToSignIn = () => {
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
                    <Lock className="h-6 w-6 text-brand" />
                  </div>
                </div>
                <CardTitle className="text-center">Reset Your Password</CardTitle>
                <p className="text-center text-sm text-muted-foreground mt-2">
                  Enter your new password below
                </p>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <Input
                    label="New Password"
                    type="password"
                    placeholder="Enter new password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    error={error && password.length < 8 ? 'Password must be at least 8 characters' : ''}
                    helperText="Must be at least 8 characters"
                    required
                    fullWidth
                  />

                  <Input
                    label="Confirm Password"
                    type="password"
                    placeholder="Confirm new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    error={error && password !== confirmPassword ? 'Passwords do not match' : ''}
                    required
                    fullWidth
                  />

                  {error && (
                    <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                      <p className="text-sm text-destructive">{error}</p>
                    </div>
                  )}

                  <Button type="submit" variant="primary" fullWidth loading={loading}>
                    Reset Password
                  </Button>
                </form>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-center mb-4">
                  <div className="h-12 w-12 rounded-full bg-success/10 flex items-center justify-center">
                    <CheckCircle className="h-6 w-6 text-success" />
                  </div>
                </div>
                <CardTitle className="text-center">Password Reset Successful</CardTitle>
                <p className="text-center text-sm text-muted-foreground mt-2">
                  Your password has been successfully reset. You can now sign in with your new password.
                </p>
              </CardHeader>
              <CardContent>
                <Button variant="primary" fullWidth onClick={handleGoToSignIn}>
                  Continue to Sign In
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
