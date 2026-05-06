import React from 'react';
import { LandingPage } from "./pages/LandingPage";
import { SignInPage } from "./pages/SignInPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { JobFeedDashboard } from "./pages/JobFeedDashboard";
import { ApplicationsDashboard } from "./pages/ApplicationsDashboard";
import { ApplicationDetailWorkspace } from "./pages/ApplicationDetailWorkspace";
import { AnswersLibrary } from "./pages/AnswersLibrary";
import { ProfileSettings } from "./pages/ProfileSettings";
import { ProfileManagementPage } from "./pages/ProfileManagementPage";
import { SimpleProfileManagementPage } from "./pages/SimpleProfileManagementPage";
import { ResumeLibrary } from "./pages/ResumeLibrary";
import { JobPreferences } from "./pages/JobPreferences";
import { ManualReviewPanel } from "./pages/ManualReviewPanel";
import { DiagnosticsWorkbench } from "./pages/DiagnosticsWorkbench";
import { BillingHub } from "./pages/BillingHub";
import { CheckoutPage } from "./pages/CheckoutPage";
import { CheckoutSuccess } from "./pages/CheckoutSuccess";
import { CheckoutCanceled } from "./pages/CheckoutCanceled";

// Simple routing for demo - in Next.js, use App Router file-based routing
export const SimpleRouter: React.FC = () => {
  const path = typeof window !== 'undefined' ? window.location.pathname : '/';

  // Public routes
  if (path === '/' || path === '') return <LandingPage />;
  if (path === '/signin') return <SignInPage />;
  if (path === '/register') return <RegisterPage />;
  if (path === '/forgot-password') return <ForgotPasswordPage />;
  if (path === '/reset-password') return <ResetPasswordPage />;

  // Checkout routes
  if (path === '/checkout') return <CheckoutPage />;
  if (path === '/checkout/success') return <CheckoutSuccess />;
  if (path === '/checkout/canceled') return <CheckoutCanceled />;

  // Authenticated routes
  if (path === '/app' || path === '/app/') return <JobFeedDashboard />;
  if (path === '/app/jobs') return <JobFeedDashboard />;
  if (path === '/app/applications') return <ApplicationsDashboard />;
  if (path.startsWith('/app/applications/') && path.endsWith('/review')) return <ManualReviewPanel />;
  if (path.startsWith('/app/applications/')) return <ApplicationDetailWorkspace />;
  if (path === '/app/answers') return <AnswersLibrary />;
  if (path === '/app/profile') return <ProfileSettings />;
  if (path === '/app/profile/career') return <SimpleProfileManagementPage />;
  if (path === '/app/resumes') return <ResumeLibrary />;
  if (path === '/app/preferences') return <JobPreferences />;
  if (path === '/app/billing') return <BillingHub />;

  // Internal routes
  if (path === '/internal/diagnostics') return <DiagnosticsWorkbench />;

  // 404
  return <LandingPage />;
};
