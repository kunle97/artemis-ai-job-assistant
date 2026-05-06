'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '../components/AppShell';
import { Button, Card, CardHeader, CardTitle, CardContent, Badge } from '../components/ui';
import {
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Clock,
  Play,
  Shield,
  Send,
  AlertTriangle,
  FileText,
  ExternalLink,
} from 'lucide-react';

interface Blocker {
  id: string;
  field: string;
  message: string;
  severity: 'error' | 'warning';
}

interface PlannedAnswer {
  question: string;
  answer: string;
  source: 'resume' | 'profile' | 'library' | 'manual';
  confidence: number;
}

const mockBlockers: Blocker[] = [
  {
    id: '1',
    field: 'Cover Letter',
    message: 'Required field not provided',
    severity: 'error',
  },
  {
    id: '2',
    field: 'Salary Expectations',
    message: 'Recommended to provide',
    severity: 'warning',
  },
  {
    id: '3',
    field: 'Start Date',
    message: 'Required field not provided',
    severity: 'error',
  },
];

const mockAnswers: PlannedAnswer[] = [
  {
    question: 'Why do you want to work here?',
    answer: "I am excited about TechCorp's mission to transform how teams collaborate...",
    source: 'library',
    confidence: 95,
  },
  {
    question: 'Describe your product management experience',
    answer: 'Over the past 5 years, I have led cross-functional teams to ship products...',
    source: 'resume',
    confidence: 90,
  },
  {
    question: 'What is your biggest professional achievement?',
    answer: 'I successfully launched a SaaS platform that grew to $10M ARR in 18 months...',
    source: 'library',
    confidence: 88,
  },
];

export const ApplicationDetailWorkspace: React.FC = () => {
  const router = useRouter();
  const [automationStatus, setAutomationStatus] = useState<'not-started' | 'running' | 'complete' | 'failed'>('not-started');
  const [authorized, setAuthorized] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const hasBlockers = mockBlockers.filter((b) => b.severity === 'error').length > 0;
  const isReadyForAutomation = !hasBlockers;
  const isReadyForSubmission = authorized && automationStatus === 'complete';

  const handleBack = () => {
    router.push('/applications');
  };

  const handleRunAutomation = () => {
    setAutomationStatus('running');
    setTimeout(() => {
      setAutomationStatus('complete');
    }, 3000);
  };

  const handleAuthorize = () => {
    setAuthorized(true);
  };

  const handleSubmit = () => {
    setSubmitting(true);
    setTimeout(() => {
      setSubmitting(false);
      router.push('/applications');
    }, 2000);
  };

  const handleReviewManually = () => {
    router.push('/applications/1/review');
  };

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button onClick={handleBack} className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-4">
            <ArrowLeft className="h-4 w-4" />
            Back to Applications
          </button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-semibold text-foreground">Senior Product Manager</h1>
              <p className="mt-1 text-lg text-muted-foreground">TechCorp Inc.</p>
            </div>
            <Badge variant={isReadyForSubmission ? 'ready' : hasBlockers ? 'blocked' : 'in-progress'}>
              {isReadyForSubmission ? 'Ready to Submit' : hasBlockers ? 'Blocked' : 'In Progress'}
            </Badge>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Application Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Application Details</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Position</span>
                    <span className="font-medium text-foreground">Senior Product Manager</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Company</span>
                    <span className="font-medium text-foreground">TechCorp Inc.</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Location</span>
                    <span className="font-medium text-foreground">San Francisco, CA</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Work Mode</span>
                    <span className="font-medium text-foreground">Hybrid</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Salary Range</span>
                    <span className="font-medium text-foreground">$150k - $200k</span>
                  </div>
                  <div className="pt-3 border-t border-border">
                    <a
                      href="#"
                      className="flex items-center gap-2 text-brand hover:underline"
                    >
                      View Job Posting
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Readiness Blockers */}
            {hasBlockers && (
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <AlertCircle className="h-5 w-5 text-destructive" />
                    <CardTitle>Readiness Blockers</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {mockBlockers.map((blocker) => (
                      <div
                        key={blocker.id}
                        className={`flex items-start gap-3 p-3 rounded-lg border ${
                          blocker.severity === 'error'
                            ? 'bg-destructive/5 border-destructive/20'
                            : 'bg-warning/5 border-warning/20'
                        }`}
                      >
                        {blocker.severity === 'error' ? (
                          <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0" />
                        ) : (
                          <AlertTriangle className="h-5 w-5 text-warning flex-shrink-0" />
                        )}
                        <div className="flex-1">
                          <p className="font-medium text-foreground">{blocker.field}</p>
                          <p className="text-sm text-muted-foreground">{blocker.message}</p>
                        </div>
                        <Button variant="outline" size="sm">
                          Resolve
                        </Button>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 pt-4 border-t border-border">
                    <Button variant="primary" fullWidth onClick={handleReviewManually}>
                      <FileText className="h-4 w-4" />
                      Review All Fields
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Planned Answers */}
            <Card>
              <CardHeader>
                <CardTitle>Planned Answers ({mockAnswers.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockAnswers.map((answer, index) => (
                    <div key={index} className="border border-border rounded-lg p-4">
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <p className="font-medium text-foreground">{answer.question}</p>
                        <Badge variant="default" size="sm">
                          {answer.source}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-2 mb-2">{answer.answer}</p>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-success"
                            style={{ width: `${answer.confidence}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground">{answer.confidence}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Actions */}
          <div className="space-y-6">
            {/* Status Timeline */}
            <Card>
              <CardHeader>
                <CardTitle>Application Workflow</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Step 1: Readiness */}
                  <div className="flex items-start gap-3">
                    {hasBlockers ? (
                      <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className="font-medium text-foreground">Readiness Check</p>
                      <p className="text-sm text-muted-foreground">
                        {hasBlockers ? `${mockBlockers.filter((b) => b.severity === 'error').length} blockers remaining` : 'All checks passed'}
                      </p>
                    </div>
                  </div>

                  {/* Step 2: Automation */}
                  <div className="flex items-start gap-3">
                    {automationStatus === 'complete' ? (
                      <CheckCircle className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                    ) : automationStatus === 'running' ? (
                      <Clock className="h-5 w-5 text-in-progress flex-shrink-0 mt-0.5 animate-spin" />
                    ) : automationStatus === 'failed' ? (
                      <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
                    ) : (
                      <Clock className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className="font-medium text-foreground">Run Automation</p>
                      <p className="text-sm text-muted-foreground">
                        {automationStatus === 'complete' ? 'Form filled successfully' :
                         automationStatus === 'running' ? 'Filling application form...' :
                         automationStatus === 'failed' ? 'Automation failed' :
                         'Not started'}
                      </p>
                    </div>
                  </div>

                  {/* Step 3: Authorization */}
                  <div className="flex items-start gap-3">
                    {authorized ? (
                      <CheckCircle className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                    ) : (
                      <Shield className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className="font-medium text-foreground">Authorize Submission</p>
                      <p className="text-sm text-muted-foreground">
                        {authorized ? 'Authorized' : 'Manual review required'}
                      </p>
                    </div>
                  </div>

                  {/* Step 4: Submit */}
                  <div className="flex items-start gap-3">
                    <Send className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-medium text-foreground">Submit Application</p>
                      <p className="text-sm text-muted-foreground">Final step</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  variant="primary"
                  fullWidth
                  onClick={handleRunAutomation}
                  disabled={!isReadyForAutomation || automationStatus === 'running' || automationStatus === 'complete'}
                  loading={automationStatus === 'running'}
                >
                  <Play className="h-4 w-4" />
                  {automationStatus === 'complete' ? 'Automation Complete' : 'Run Automation'}
                </Button>

                {automationStatus === 'complete' && !authorized && (
                  <div className="p-4 rounded-lg bg-warning/10 border border-warning/20">
                    <div className="flex items-start gap-2 mb-3">
                      <Shield className="h-5 w-5 text-warning flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-foreground">Authorization Required</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Review the filled application and authorize submission
                        </p>
                      </div>
                    </div>
                    <Button variant="primary" fullWidth onClick={handleAuthorize}>
                      <Shield className="h-4 w-4" />
                      I Authorize Submission
                    </Button>
                  </div>
                )}

                {authorized && (
                  <div className="p-4 rounded-lg bg-success/10 border border-success/20">
                    <div className="flex items-center gap-2 mb-3">
                      <CheckCircle className="h-5 w-5 text-success" />
                      <p className="text-sm font-medium text-foreground">Ready to Submit</p>
                    </div>
                    <Button variant="primary" fullWidth onClick={handleSubmit} loading={submitting}>
                      <Send className="h-4 w-4" />
                      Submit Application
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Safety Notice */}
            <Card variant="outlined" className="bg-brand/5 border-brand/20">
              <CardContent className="pt-6">
                <div className="flex gap-3">
                  <Shield className="h-5 w-5 text-brand flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-foreground mb-1">You're in control</p>
                    <p className="text-xs text-muted-foreground">
                      Artemis never submits applications without your explicit authorization.
                      Review everything before you approve.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
};
