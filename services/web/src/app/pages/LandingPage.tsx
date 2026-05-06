'use client';
import React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '../components/ui';
import { CheckCircle, Shield, Sparkles, Briefcase, FileText, Target } from 'lucide-react';
import { PricingSection } from '../components/PricingSection';

export const LandingPage: React.FC = () => {
  const router = useRouter();

  const handleGetStarted = () => {
    router.push('/register');
  };

  const handleSignIn = () => {
    router.push('/signin');
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto max-w-7xl px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-8 w-8 text-brand" />
              <span className="text-2xl font-semibold text-foreground">Artemis</span>
            </div>
            <div className="flex items-center gap-4">
              <Button variant="ghost" onClick={handleSignIn}>
                Sign In
              </Button>
              <Button variant="primary" onClick={handleGetStarted}>
                Get Started
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-24 overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: 'url(https://images.unsplash.com/photo-1758876202527-78553b7769ee?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1920)',
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-br from-background/85 via-background/80 to-background/75" />
        <div className="relative mx-auto max-w-7xl px-6">
          <div className="text-center">
            <h1 className="text-5xl font-semibold tracking-tight text-foreground sm:text-6xl">
              Your AI-Powered
              <span className="block text-brand">Job Application Copilot</span>
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
              Artemis helps ambitious job seekers manage their search, track applications, and automate repetitive
              tasks—while keeping you in complete control. Never miss an opportunity again.
            </p>
            <div className="mt-10 flex items-center justify-center gap-4">
              <Button variant="primary" size="lg" onClick={handleGetStarted}>
                Get Started Free
              </Button>
              <Button variant="outline" size="lg">
                Watch Demo
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="relative py-24 bg-gradient-to-br from-secondary/30 via-background to-brand/5 overflow-hidden">
        <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, currentColor 1px, transparent 0)', backgroundSize: '32px 32px' }}></div>
        <div className="relative">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center">
            <h2 className="text-3xl font-semibold text-foreground">How Artemis Works</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              A complete workflow designed for modern job seekers
            </p>
          </div>
          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                step: '1',
                title: 'Upload Your Resume',
                description: 'Artemis parses your resume and builds your candidate profile automatically.',
                icon: FileText,
              },
              {
                step: '2',
                title: 'Discover Opportunities',
                description: 'Get a personalized job feed based on your skills, preferences, and career goals.',
                icon: Target,
              },
              {
                step: '3',
                title: 'Track Applications',
                description: 'Manage all your applications in one place with clear status tracking.',
                icon: Briefcase,
              },
              {
                step: '4',
                title: 'Reuse Your Answers',
                description: 'Save time by building a library of reusable answers to common application questions.',
                icon: Sparkles,
              },
              {
                step: '5',
                title: 'Automate Safely',
                description: 'Let Artemis help fill out forms while you maintain complete control and authorization.',
                icon: CheckCircle,
              },
              {
                step: '6',
                title: 'Submit With Confidence',
                description: 'Review and authorize every submission. Artemis never submits without your approval.',
                icon: Shield,
              },
            ].map((item) => (
              <div key={item.step} className="relative">
                <div className="flex flex-col gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand text-brand-foreground">
                    <span className="text-xl font-semibold">{item.step}</span>
                  </div>
                  <h3 className="text-xl font-semibold text-foreground">{item.title}</h3>
                  <p className="text-muted-foreground">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        </div>
      </section>

      {/* Value Props */}
      <section className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-background via-brand/5 to-background"></div>
        <div className="relative">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center">
            <h2 className="text-3xl font-semibold text-foreground">Why Choose Artemis</h2>
          </div>
          <div className="mt-16 grid gap-12 lg:grid-cols-2">
            <div className="flex gap-4">
              <Shield className="h-8 w-8 flex-shrink-0 text-brand" />
              <div>
                <h3 className="text-xl font-semibold text-foreground">You Stay in Control</h3>
                <p className="mt-2 text-muted-foreground">
                  Artemis is designed with safety and transparency at its core. Every application requires manual
                  authorization before submission. You review, you approve, you submit—not the AI.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <Sparkles className="h-8 w-8 flex-shrink-0 text-brand" />
              <div>
                <h3 className="text-xl font-semibold text-foreground">AI That Actually Helps</h3>
                <p className="mt-2 text-muted-foreground">
                  Intelligent resume parsing, reusable answer matching, and form-fill assistance save you hours of
                  repetitive work while keeping quality high.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <Briefcase className="h-8 w-8 flex-shrink-0 text-brand" />
              <div>
                <h3 className="text-xl font-semibold text-foreground">Complete Application Tracking</h3>
                <p className="mt-2 text-muted-foreground">
                  See all your applications in one dashboard. Track status, readiness, and next steps. Never lose track
                  of an opportunity again.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <Target className="h-8 w-8 flex-shrink-0 text-brand" />
              <div>
                <h3 className="text-xl font-semibold text-foreground">Built for Ambitious Careers</h3>
                <p className="mt-2 text-muted-foreground">
                  This isn't a generic job board. Artemis is a workflow platform for serious job seekers who want to
                  apply faster, smarter, and more effectively.
                </p>
              </div>
            </div>
          </div>
        </div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="relative py-16 overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: 'url(https://images.unsplash.com/photo-1774898989484-0b9becf69efb?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1920)',
          }}
        />
        <div className="absolute inset-0 bg-background/96" />
        <div className="relative">
          <div className="mx-auto max-w-4xl px-6 text-center">
            <Shield className="mx-auto h-12 w-12 text-brand" />
            <h2 className="mt-6 text-2xl font-semibold text-foreground">Your Data, Your Control</h2>
            <p className="mt-4 text-muted-foreground">
              Artemis uses your data only to help you with your job search. We never share your information with
              employers without your explicit consent. Your resume, profile, and application history remain private and
              secure.
            </p>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <PricingSection />

      {/* CTA Section */}
      <section className="relative py-24 bg-gradient-to-t from-brand/5 to-background overflow-hidden">
        <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(circle, currentColor 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>
        <div className="relative mx-auto max-w-4xl px-6 text-center">
          <h2 className="text-3xl font-semibold text-foreground">Ready to transform your job search?</h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Join Artemis today and take control of your career journey.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Button variant="primary" size="lg" onClick={handleGetStarted}>
              Get Started Free
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-12">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-brand" />
              <span className="text-lg font-semibold text-foreground">Artemis</span>
            </div>
            <p className="text-sm text-muted-foreground">© 2026 Artemis. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};
