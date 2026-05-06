// RegisterPage: account creation and handoff to onboarding component.
'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Input, Card } from '../components/ui';
import { Sparkles } from 'lucide-react';
import {
  loginUser,
  registerUser,
  type RegisterUserPayload,
} from '../../services/auth/auth.service';
import { RegistrationOnboarding } from '../components/RegistrationOnboarding';

// ── Types ────────────────────────────────────────────────────────────────────

interface FieldErrors {
  firstName?: string;
  lastName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validateForm(data: {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
}): FieldErrors {
  const errors: FieldErrors = {};
  if (!data.firstName.trim()) errors.firstName = 'First name is required';
  if (!data.lastName.trim()) errors.lastName = 'Last name is required';
  if (!data.email.trim()) {
    errors.email = 'Email is required';
  } else if (!EMAIL_RE.test(data.email)) {
    errors.email = 'Enter a valid email address';
  }
  if (!data.password) {
    errors.password = 'Password is required';
  } else if (data.password.length < 8) {
    errors.password = 'Password must be at least 8 characters';
  }
  if (!data.confirmPassword) {
    errors.confirmPassword = 'Please confirm your password';
  } else if (data.password !== data.confirmPassword) {
    errors.confirmPassword = 'Passwords do not match';
  }
  return errors;
}

// ── Component ─────────────────────────────────────────────────────────────────

export const RegisterPage: React.FC = () => {
  const router = useRouter();

  // Registration state
  const [step, setStep] = useState<'register' | 'onboarding'>('register');
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);

  // ── Registration handlers ─────────────────────────────────────────────────

  const handleFieldChange = (field: keyof typeof formData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear per-field error on edit
    if (fieldErrors[field]) {
      setFieldErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGlobalError(null);

    const errors = validateForm(formData);
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    setLoading(true);
    try {
      const payload: RegisterUserPayload = {
        first_name: formData.firstName,
        last_name: formData.lastName,
        email: formData.email,
        password: formData.password,
      };

      await registerUser(payload);
      const tokens = await loginUser({
        email: formData.email,
        password: formData.password,
      });

      if (typeof window !== 'undefined') {
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);
      }

      setStep('onboarding');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to connect to the server. Please try again.';
      setGlobalError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleEnterDashboard = () => {
    router.push('/jobs');
  };

  const handleGoToSignIn = () => {
    router.push('/signin');
  };

  const handleBackToHome = () => {
    router.push('/');
  };

  if (step === 'onboarding') {
    return <RegistrationOnboarding firstName={formData.firstName} onComplete={handleEnterDashboard} />;
  }

  // ── Registration form view ─────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4 sm:px-6 py-12">
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
          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            {/* Global error (e.g. duplicate email, network failure) */}
            {globalError && (
              <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20">
                <p className="text-sm text-destructive">{globalError}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <Input
                type="text"
                label="First Name"
                placeholder="John"
                value={formData.firstName}
                onChange={(e) => handleFieldChange('firstName', e.target.value)}
                fullWidth
                autoComplete="given-name"
                error={fieldErrors.firstName}
              />
              <Input
                type="text"
                label="Last Name"
                placeholder="Doe"
                value={formData.lastName}
                onChange={(e) => handleFieldChange('lastName', e.target.value)}
                fullWidth
                autoComplete="family-name"
                error={fieldErrors.lastName}
              />
            </div>

            <Input
              type="email"
              label="Email"
              placeholder="you@example.com"
              value={formData.email}
              onChange={(e) => handleFieldChange('email', e.target.value)}
              fullWidth
              autoComplete="email"
              error={fieldErrors.email}
            />

            <Input
              type="password"
              label="Password"
              placeholder="Create a strong password"
              value={formData.password}
              onChange={(e) => handleFieldChange('password', e.target.value)}
              fullWidth
              autoComplete="new-password"
              helperText={fieldErrors.password ? undefined : 'At least 8 characters'}
              error={fieldErrors.password}
            />

            <Input
              type="password"
              label="Confirm Password"
              placeholder="Re-enter your password"
              value={formData.confirmPassword}
              onChange={(e) => handleFieldChange('confirmPassword', e.target.value)}
              fullWidth
              autoComplete="new-password"
              error={fieldErrors.confirmPassword}
            />

            <div className="flex items-start gap-2">
              <input
                type="checkbox"
                id="terms"
                checked={termsAccepted}
                onChange={(e) => setTermsAccepted(e.target.checked)}
                className="h-4 w-4 rounded border-border text-brand mt-1 cursor-pointer"
              />
              <label htmlFor="terms" className="text-sm text-muted-foreground cursor-pointer">
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

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              loading={loading}
              disabled={!termsAccepted}
            >
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

