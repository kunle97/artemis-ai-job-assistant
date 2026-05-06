'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { PlanCard, IntervalToggle, BillingInterval } from './billing';
import { ChevronDown, ChevronUp } from 'lucide-react';

const pricingPlans = {
  free: {
    name: 'Free',
    tier: 'free' as const,
    priceMonthly: 0,
    priceYearly: 0,
    features: [
      { text: '10 job scans per month', included: true },
      { text: '3 applications per month', included: true },
      { text: '5 automation fills per month', included: true },
      { text: 'Manual review always required', included: true },
      { text: 'Priority queue', included: false },
      { text: 'Advanced analytics', included: false },
    ],
  },
  premium: {
    name: 'Premium',
    tier: 'premium' as const,
    priceMonthly: 29,
    priceYearly: 24,
    features: [
      { text: '100 job scans per month', included: true },
      { text: '20 applications per month', included: true },
      { text: '50 automation fills per month', included: true },
      { text: 'Optional manual review skip', included: true },
      { text: 'Priority queue', included: true },
      { text: 'Advanced analytics', included: false },
    ],
  },
  pro: {
    name: 'Pro',
    tier: 'pro' as const,
    priceMonthly: 79,
    priceYearly: 66,
    features: [
      { text: 'Unlimited job scans', included: true },
      { text: 'Unlimited applications', included: true },
      { text: 'Unlimited automation fills', included: true },
      { text: 'Optional manual review skip', included: true },
      { text: 'Priority queue', included: true },
      { text: 'Advanced analytics', included: true },
    ],
  },
};

const faqs = [
  {
    question: 'How does billing work?',
    answer:
      'We use Stripe for secure payment processing. You can pay monthly or yearly. Yearly plans save you up to 20%. Your subscription renews automatically unless you cancel.',
  },
  {
    question: 'Do you offer a free trial?',
    answer:
      'Yes! Premium and Pro plans come with a 14-day free trial. No credit card required to start. You can cancel anytime during the trial with no charge.',
  },
  {
    question: 'Can I use promo codes?',
    answer:
      'Yes, we accept promo codes during checkout. Enter your code on the payment page before completing your purchase.',
  },
  {
    question: 'When does my subscription cancel?',
    answer:
      'If you cancel, your subscription remains active until the end of your current billing period. You retain full access until then. After that, you will downgrade to the Free plan.',
  },
  {
    question: 'What happens if my payment fails?',
    answer:
      'If a payment fails, we will attempt to charge your card again over the next few days. Your account will be marked as past due. If payment continues to fail, your account may be suspended. Update your payment method in the billing portal to resolve.',
  },
];

export const PricingSection: React.FC = () => {
  const router = useRouter();
  const [interval, setInterval] = useState<BillingInterval>('monthly');
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

  const handleSelectPlan = (tier: string) => {
    if (tier === 'free') {
      router.push('/register');
    } else {
      router.push(`/checkout?plan=${tier}&interval=${interval}`);
    }
  };

  return (
    <>
      {/* Pricing Section */}
      <section className="py-24" id="pricing">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-semibold text-foreground">Simple, Transparent Pricing</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Choose the plan that fits your job search needs
            </p>
          </div>

          <div className="flex flex-col items-center mb-12">
            <IntervalToggle interval={interval} onChange={setInterval} yearlyDiscount={17} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <PlanCard
              {...pricingPlans.free}
              interval={interval}
              onSelect={() => handleSelectPlan('free')}
            />
            <PlanCard
              {...pricingPlans.premium}
              interval={interval}
              popular
              onSelect={() => handleSelectPlan('premium')}
            />
            <PlanCard
              {...pricingPlans.pro}
              interval={interval}
              onSelect={() => handleSelectPlan('pro')}
            />
          </div>

          <div className="mt-12 text-center">
            <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
              <span className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-success" />
                No hidden fees
              </span>
              <span className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-success" />
                Cancel anytime
              </span>
              <span className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-success" />
                Secure checkout via Stripe
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="bg-secondary/50 py-24">
        <div className="mx-auto max-w-3xl px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-semibold text-foreground">Frequently Asked Questions</h2>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <div key={index} className="bg-card border border-border rounded-lg overflow-hidden">
                <button
                  onClick={() => setExpandedFaq(expandedFaq === index ? null : index)}
                  className="w-full flex items-center justify-between p-6 text-left hover:bg-secondary/50 transition-colors"
                >
                  <h3 className="font-semibold text-foreground pr-4">{faq.question}</h3>
                  {expandedFaq === index ? (
                    <ChevronUp className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                  )}
                </button>
                {expandedFaq === index && (
                  <div className="px-6 pb-6">
                    <p className="text-muted-foreground">{faq.answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
};
