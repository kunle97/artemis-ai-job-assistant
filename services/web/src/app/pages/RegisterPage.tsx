'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Input, Card } from '../components/ui';
import { Sparkles, CheckCircle, Circle } from 'lucide-react';

export const RegisterPage: React.FC = () => {
  const router = useRouter();
  const [step, setStep] = useState<'register' | 'onboarding'>('register');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setStep('onboarding');
    }, 1000);
  };

  const handleCompleteOnboarding = () => {
    router.push('/jobs');
  };

  const handleSkipOnboarding = () => {
    router.push('/jobs');
  };

  const handleGoToSignIn = () => {
    router.push('/signin');
  };

  const handleBackToHome = () => {
    router.push('/');
  };

  if (step === 'onboarding') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-2xl">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Sparkles className="h-10 w-10 text-brand" />
              <span className="text-3xl font-semibold text-foreground">Artemis</span>
            </div>
            <h1 className="text-2xl font-semibold text-foreground">Welcome to Artemis!</h1>
            <p className="mt-2 text-muted-foreground">Let's get your profile set up in just a few steps</p>
          </div>

          <Card>
            <div className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-start gap-4 p-4 rounded-lg border border-border hover:bg-secondary/50 transition-colors cursor-pointer">
                  <Circle className="h-6 w-6 text-muted-foreground flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-foreground">Complete your profile</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      Add your professional information and career goals
                    </p>
                  </div>
                  <Button variant="outline" size="sm">
                    Start
                  </Button>
                </div>

                <div className="flex items-start gap-4 p-4 rounded-lg border border-border hover:bg-secondary/50 transition-colors cursor-pointer">
                  <Circle className="h-6 w-6 text-muted-foreground flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-foreground">Upload your resume</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      Let Artemis parse your resume and auto-fill your profile
                    </p>
                  </div>
                  <Button variant="outline" size="sm">
                    Upload
                  </Button>
                </div>

                <div className="flex items-start gap-4 p-4 rounded-lg border border-border hover:bg-secondary/50 transition-colors cursor-pointer">
                  <Circle className="h-6 w-6 text-muted-foreground flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-foreground">Set job preferences</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      Tell us what kind of roles you're looking for
                    </p>
                  </div>
                  <Button variant="outline" size="sm">
                    Configure
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-between pt-6 border-t border-border">
                <button onClick={handleSkipOnboarding} className="text-sm text-muted-foreground hover:text-foreground">
                  Skip for now
                </button>
                <Button variant="primary" onClick={handleCompleteOnboarding}>
                  Continue to Dashboard
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Sparkles className="h-10 w-10 text-brand" />
            <span className="text-3xl font-semibold text-foreground">Artemis</span>
          </div>
          <h1 className="text-2xl font-semibold text-foreground">Create your account</h1>
          <p className="mt-2 text-muted-foreground">Start your journey to better job applications</p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            <Input
              type="text"
              label="Full Name"
              placeholder="John Doe"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              fullWidth
            />

            <Input
              type="email"
              label="Email"
              placeholder="you@example.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              fullWidth
              autoComplete="email"
            />

            <Input
              type="password"
              label="Password"
              placeholder="Create a strong password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
              fullWidth
              autoComplete="new-password"
              helperText="At least 8 characters"
            />

            <Input
              type="password"
              label="Confirm Password"
              placeholder="Re-enter your password"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              required
              fullWidth
              autoComplete="new-password"
            />

            <div className="flex items-start gap-2">
              <input type="checkbox" required className="h-4 w-4 rounded border-border text-brand mt-1" />
              <label className="text-sm text-muted-foreground">
                I agree to the{' '}
                <a href="#" className="text-brand hover:underline">
                  Terms of Service
                </a>{' '}
                and{' '}
                <a href="#" className="text-brand hover:underline">
                  Privacy Policy
                </a>
              </label>
            </div>

            <Button type="submit" variant="primary" size="lg" fullWidth loading={loading}>
              Create Account
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              Already have an account?{' '}
              <button onClick={handleGoToSignIn} className="text-brand hover:underline font-medium">
                Sign in
              </button>
            </p>
          </div>
        </Card>

        <div className="mt-6 text-center">
          <button onClick={handleBackToHome} className="text-sm text-muted-foreground hover:text-foreground">
            ← Back to home
          </button>
        </div>
      </div>
    </div>
  );
};
