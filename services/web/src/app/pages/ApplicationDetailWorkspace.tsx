'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { AppShell } from '../components/AppShell';
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from '../components/ui';
import {
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  CheckCircle,
  Clock,
  ExternalLink,
  Play,
  RefreshCw,
  Send,
  Shield,
} from 'lucide-react';
import { getStoredAccessToken } from '../../services/auth/auth.service';
import {
  authorizeApplication,
  getApplicationById,
  getApplicationReadiness,
  getApplicationStatus,
  getJobById,
  runApplicationPipeline,
  submitApplication,
  type ApplicationReadinessRecord,
  type ApplicationRecord,
  type ApplicationStatusRecord,
} from '../../services/applications/application-workspace.service';

type ReadinessSeverity = 'error' | 'warning' | 'info';
type AutomationState = 'idle' | 'queued' | 'running' | 'success' | 'failure';

interface ReadinessItem {
  key: string;
  title: string;
  description: string;
  severity: ReadinessSeverity;
  ctaLabel: string;
  ctaPath: string;
}

function normalizeStatus(status: string | undefined): string {
  return (status || '').trim().toLowerCase();
}

function formatMissingItem(item: string): string {
  switch (item) {
    case 'candidate_profile':
      return 'Candidate profile missing';
    case 'resume':
      return 'Resume missing';
    default:
      return item.replace(/_/g, ' ');
  }
}

function buildReadinessItems(
  readiness: ApplicationReadinessRecord,
  status: ApplicationStatusRecord,
): ReadinessItem[] {
  const items: ReadinessItem[] = readiness.missing_items.map((item) => ({
    key: item,
    title: formatMissingItem(item),
    description:
      item === 'candidate_profile'
        ? 'Complete your profile before automation can safely run.'
        : item === 'resume'
          ? 'Upload a resume so Artemis can resolve application fields.'
          : 'This required data is missing for automation.',
    severity: 'error',
    ctaLabel: item === 'candidate_profile' ? 'Open Profile' : item === 'resume' ? 'Open Resume Library' : 'Review',
    ctaPath: item === 'candidate_profile' ? '/profile' : item === 'resume' ? '/resumes' : '/applications',
  }));

  const normalizedStatus = (status.status || '').trim().toLowerCase();
  const reviewActionableStatuses = new Set([
    'filled',
    'awaiting_submission',
    'ready_to_submit',
    'needs_review',
    'ready',
  ]);

  if (status.manual_review_required && reviewActionableStatuses.has(normalizedStatus)) {
    items.push({
      key: 'manual_review_required',
      title: 'Manual review required',
      description: 'Automation output must be reviewed before authorization.',
      severity: 'warning',
      ctaLabel: 'Review Fields',
      ctaPath: `/applications/${status.application_id}/review`,
    });
  }

  return items;
}

export const ApplicationDetailWorkspace: React.FC = () => {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const applicationId = String(params?.id || '');
  const token = getStoredAccessToken();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [application, setApplication] = useState<ApplicationRecord | null>(null);
  const [status, setStatus] = useState<ApplicationStatusRecord | null>(null);
  const [readiness, setReadiness] = useState<ApplicationReadinessRecord | null>(null);
  const [jobTitle, setJobTitle] = useState<string>('Application');
  const [companyName, setCompanyName] = useState<string>('Unknown company');
  const [locationLabel, setLocationLabel] = useState<string>('Unknown location');
  const [workModeLabel, setWorkModeLabel] = useState<string>('Unknown work mode');
  const [jobUrl, setJobUrl] = useState<string | null>(null);

  const [automationState, setAutomationState] = useState<AutomationState>('idle');
  const [runTaskId, setRunTaskId] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  const [running, setRunning] = useState(false);
  const [authorizing, setAuthorizing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [confirmSubmit, setConfirmSubmit] = useState(false);

  const loadWorkspace = useCallback(async () => {
    if (!token || !applicationId) {
      setError('Please sign in and choose a valid application.');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const [applicationRecord, statusRecord, readinessRecord] = await Promise.all([
        getApplicationById(token, applicationId),
        getApplicationStatus(token, applicationId),
        getApplicationReadiness(token, applicationId),
      ]);

      const job = await getJobById(token, applicationRecord.job_id);

      setApplication(applicationRecord);
      setStatus(statusRecord);
      setReadiness(readinessRecord);

      if (job) {
        setJobTitle(job.title || 'Application');
        setCompanyName(job.company_name || 'Unknown company');
        setLocationLabel(job.location || 'Unknown location');
        setWorkModeLabel(job.workplace_type || 'Unknown work mode');
        setJobUrl(job.apply_url || null);
      } else {
        setJobTitle('Application');
        setCompanyName('Unknown company');
        setLocationLabel('Unknown location');
        setWorkModeLabel('Unknown work mode');
        setJobUrl(null);
      }

      const normalizedStatus = normalizeStatus(statusRecord.status);
      if (normalizedStatus === 'failed' || statusRecord.failure_reason) {
        setAutomationState('failure');
      } else if (
        ['running', 'queued', 'in_progress', 'inspecting', 'inspected', 'planning', 'planned', 'filling'].includes(normalizedStatus)
      ) {
        setAutomationState('running');
      } else if (
        normalizedStatus === 'filled'
        || normalizedStatus === 'authorized'
        || normalizedStatus === 'submitted'
        || normalizedStatus === 'ready_to_submit'
      ) {
        setAutomationState('success');
      } else {
        setAutomationState('idle');
      }
    } catch (loadError) {
      const message = loadError instanceof Error ? loadError.message : 'Failed to load application workspace.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [applicationId, token]);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  const readinessItems = useMemo(() => {
    if (!readiness || !status) return [];
    return buildReadinessItems(readiness, status);
  }, [readiness, status]);

  const errorBlockers = readinessItems.filter((item) => item.severity === 'error');
  const warningBlockers = readinessItems.filter((item) => item.severity === 'warning');
  const infoBlockers = readinessItems.filter((item) => item.severity === 'info');

  const normalizedStatus = normalizeStatus(status?.status);
  const submitted = normalizedStatus === 'submitted';
  const isFormFillingStage = normalizedStatus === 'filling';
  const authorized = Boolean(status?.is_authorized_to_submit);
  const hasBlockingReadiness = errorBlockers.length > 0;
  const automationComplete = automationState === 'success';
  const automationRunning = automationState === 'running' || automationState === 'queued';
  const automationFailed = automationState === 'failure';

  const automationNeedsReview = automationComplete && (
    (status?.manual_review_required ?? false) ||
    warningBlockers.length > 0 ||
    infoBlockers.length > 0
  );

  const canRunAutomation = !loading && !hasBlockingReadiness && !automationRunning && !submitted;
  const canAuthorize = automationComplete && !authorized && !submitted;
  const canSubmit = automationComplete && authorized && !hasBlockingReadiness && !submitted;

  const readinessVerdict: 'ready' | 'blocked' | 'needs review' = hasBlockingReadiness
    ? 'blocked'
    : warningBlockers.length > 0 || infoBlockers.length > 0
      ? 'needs review'
      : 'ready';

  const workflowNextAction = submitted
    ? 'Application submitted.'
    : hasBlockingReadiness
      ? 'Resolve readiness blockers first.'
      : automationRunning
        ? 'Wait for automation to finish.'
        : !automationComplete
          ? 'Run automation.'
          : !authorized
            ? 'Authorize submission.'
            : 'Submit application.';

  const handleRunAutomation = async () => {
    if (!token || !applicationId) return;
    setRunning(true);
    setRunError(null);
    setAutomationState('queued');

    try {
      const dispatch = await runApplicationPipeline(token, applicationId);
      setRunTaskId(dispatch.task_id);
      setAutomationState(dispatch.status === 'queued' ? 'queued' : 'running');
      toast.success('Automation queued', {
        description: 'The automation pipeline has been dispatched.',
      });
      await loadWorkspace();
    } catch (runPipelineError) {
      const message = runPipelineError instanceof Error ? runPipelineError.message : 'Automation dispatch failed.';
      setRunError(message);
      setAutomationState('failure');
      toast.error('Automation failed', { description: message });
    } finally {
      setRunning(false);
    }
  };

  const handleAuthorize = async () => {
    if (!token || !applicationId) return;
    setAuthorizing(true);
    try {
      const updated = await authorizeApplication(token, applicationId);
      setApplication(updated);
      toast.success('Submission authorized', {
        description: 'Authorization is separate from final submission.',
      });
      await loadWorkspace();
    } catch (authorizeError) {
      const message = authorizeError instanceof Error ? authorizeError.message : 'Failed to authorize submission.';
      toast.error('Authorization failed', { description: message });
    } finally {
      setAuthorizing(false);
    }
  };

  const handleSubmit = async () => {
    if (!token || !applicationId) return;
    setSubmitting(true);
    try {
      const updated = await submitApplication(token, applicationId);
      setApplication(updated);
      setConfirmSubmit(false);
      toast.success('Application submitted', {
        description: 'Submission has been completed successfully.',
      });
      await loadWorkspace();
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : 'Failed to submit application.';
      toast.error('Submission failed', { description: message });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div className="max-w-7xl mx-auto space-y-6 animate-pulse">
          <div className="h-20 rounded-lg bg-muted" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 h-96 rounded-lg bg-muted" />
            <div className="h-96 rounded-lg bg-muted" />
          </div>
        </div>
      </AppShell>
    );
  }

  if (error || !application || !status || !readiness) {
    return (
      <AppShell>
        <div className="max-w-4xl mx-auto space-y-4">
          <Button variant="outline" onClick={() => router.push('/applications')}>
            <ArrowLeft className="h-4 w-4" />
            Back to Applications
          </Button>
          <Card className="border-destructive/30 bg-destructive/5">
            <CardContent className="pt-6 space-y-4">
              <p className="text-sm text-destructive">{error || 'Unable to load application workspace.'}</p>
              <Button variant="outline" onClick={() => void loadWorkspace()}>
                <RefreshCw className="h-4 w-4" />
                Retry
              </Button>
            </CardContent>
          </Card>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <button
              onClick={() => router.push('/applications')}
              className="mb-3 flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Applications
            </button>
            <h1 className="text-3xl font-semibold text-foreground">{jobTitle}</h1>
            <p className="text-lg text-muted-foreground mt-1">{companyName}</p>
          </div>
          <Badge variant={submitted ? 'success' : hasBlockingReadiness ? 'blocked' : 'in-progress'} size="lg">
            {submitted ? 'Submitted' : hasBlockingReadiness ? 'Blocked' : 'In Progress'}
          </Badge>
        </div>

        <Card>
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 text-sm">
              <p className="text-muted-foreground">
                Application ID:
                <span className="ml-2 text-foreground font-medium">{application.id}</span>
              </p>
              <p className="text-muted-foreground">
                Location:
                <span className="ml-2 text-foreground font-medium">{locationLabel}</span>
              </p>
              <p className="text-muted-foreground">
                Work Mode:
                <span className="ml-2 text-foreground font-medium">{workModeLabel}</span>
              </p>
              <p className="text-muted-foreground">
                Last Updated:
                <span className="ml-2 text-foreground font-medium">{new Date(application.updated_at).toLocaleString()}</span>
              </p>
              <p className="text-muted-foreground">
                Lifecycle Status:
                <span className="ml-2 text-foreground font-medium">{status.status}</span>
              </p>
              {jobUrl ? (
                <a href={jobUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-brand hover:underline">
                  View Job Posting
                  <ExternalLink className="h-4 w-4" />
                </a>
              ) : (
                <p className="text-muted-foreground">Job posting URL unavailable</p>
              )}
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card className={readinessVerdict === 'blocked' ? 'border-destructive/30' : readinessVerdict === 'needs review' ? 'border-warning/30' : 'border-success/30'}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {readinessVerdict === 'blocked' ? (
                    <AlertCircle className="h-5 w-5 text-destructive" />
                  ) : readinessVerdict === 'needs review' ? (
                    <AlertTriangle className="h-5 w-5 text-warning" />
                  ) : (
                    <CheckCircle className="h-5 w-5 text-success" />
                  )}
                  Readiness: {readinessVerdict}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">{workflowNextAction}</p>

                {readinessItems.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No blockers detected.</p>
                ) : (
                  <div className="space-y-3">
                    {readinessItems.map((item) => (
                      <div
                        key={item.key}
                        className={`rounded-lg border p-3 flex items-start justify-between gap-3 ${
                          item.severity === 'error'
                            ? 'border-destructive/30 bg-destructive/5'
                            : item.severity === 'warning'
                              ? 'border-warning/30 bg-warning/5'
                              : 'border-info/30 bg-info/5'
                        }`}
                      >
                        <div>
                          <p className="font-medium text-foreground">{item.title}</p>
                          <p className="text-sm text-muted-foreground">{item.description}</p>
                        </div>
                        <Button variant="outline" size="sm" onClick={() => router.push(item.ctaPath)}>
                          {item.ctaLabel}
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

          </div>

          <div className="space-y-6 lg:sticky lg:top-20 h-fit">
            <Card>
              <CardHeader>
                <CardTitle>Workflow Timeline</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-start gap-3">
                  {hasBlockingReadiness ? (
                    <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
                  ) : (
                    <CheckCircle className="h-5 w-5 text-success mt-0.5" />
                  )}
                  <div>
                    <p className="font-medium text-foreground">Readiness</p>
                    <p className="text-sm text-muted-foreground">
                      {hasBlockingReadiness ? 'Blocked by missing prerequisites.' : 'Ready for automation.'}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  {automationRunning ? (
                    <Clock className="h-5 w-5 text-info mt-0.5 animate-spin" />
                  ) : automationFailed ? (
                    <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
                  ) : automationNeedsReview ? (
                    <AlertTriangle className="h-5 w-5 text-warning mt-0.5" />
                  ) : automationComplete ? (
                    <CheckCircle className="h-5 w-5 text-success mt-0.5" />
                  ) : (
                    <Clock className="h-5 w-5 text-muted-foreground mt-0.5" />
                  )}
                  <div>
                    <p className="font-medium text-foreground">Automation</p>
                    <p className="text-sm text-muted-foreground">
                      {automationRunning
                        ? `Queued/running${runTaskId ? ` - task ${runTaskId}` : ''}`
                        : automationFailed
                          ? `Failed${status.failure_reason ? ` - ${status.failure_reason}` : ''}`
                          : automationNeedsReview
                            ? 'Completed — needs review'
                            : automationComplete
                              ? 'Completed'
                              : 'Not started'}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  {authorized ? (
                    <CheckCircle className="h-5 w-5 text-success mt-0.5" />
                  ) : (
                    <Shield className="h-5 w-5 text-muted-foreground mt-0.5" />
                  )}
                  <div>
                    <p className="font-medium text-foreground">Authorization</p>
                    <p className="text-sm text-muted-foreground">
                      {authorized ? 'Authorized for final submission.' : 'Manual authorization required.'}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  {submitted ? (
                    <CheckCircle className="h-5 w-5 text-success mt-0.5" />
                  ) : canSubmit ? (
                    <Clock className="h-5 w-5 text-info mt-0.5" />
                  ) : (
                    <Send className="h-5 w-5 text-muted-foreground mt-0.5" />
                  )}
                  <div>
                    <p className="font-medium text-foreground">Submission</p>
                    <p className="text-sm text-muted-foreground">
                      {submitted ? 'Submitted.' : canSubmit ? 'Ready to submit.' : 'Blocked until prerequisites are met.'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Run Automation</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground">Runs form-fill automation only. This does not authorize or submit.</p>
                {automationRunning ? (
                  <div className="rounded-lg border border-info/30 bg-info/5 px-3 py-2">
                    <p className="text-xs text-info inline-flex items-center gap-2">
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      {isFormFillingStage
                        ? 'Automation is actively filling the external form right now.'
                        : 'Automation is in progress. Please wait for completion before running again.'}
                    </p>
                  </div>
                ) : null}
                <Button
                  variant="primary"
                  fullWidth
                  disabled={!canRunAutomation || running}
                  loading={running}
                  onClick={handleRunAutomation}
                >
                  {automationRunning ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  {automationRunning
                    ? (isFormFillingStage ? 'Filling Form...' : 'Automation Running...')
                    : (automationComplete ? 'Run Again' : 'Run Automation')}
                </Button>
                {runError ? <p className="text-xs text-destructive">{runError}</p> : null}
              </CardContent>
            </Card>

            <Card className="border-warning/30 bg-warning/5">
              <CardHeader>
                <CardTitle>Authorization</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground">Authorization confirms you reviewed the automation output. It is not submission.</p>
                <Button
                  variant="outline"
                  fullWidth
                  disabled={!canAuthorize || authorizing}
                  loading={authorizing}
                  onClick={handleAuthorize}
                >
                  <Shield className="h-4 w-4" />
                  {authorized ? 'Already Authorized' : 'Authorize Submission'}
                </Button>
              </CardContent>
            </Card>

            <Card className="border-brand/30 bg-brand/5">
              <CardHeader>
                <CardTitle>Final Submission</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground">Final and user-controlled step. Artemis will not submit without your explicit action.</p>
                {!confirmSubmit ? (
                  <Button
                    variant="primary"
                    fullWidth
                    disabled={!canSubmit || submitting}
                    onClick={() => setConfirmSubmit(true)}
                  >
                    <Send className="h-4 w-4" />
                    Submit Application
                  </Button>
                ) : (
                  <div className="space-y-2">
                    <p className="text-xs text-muted-foreground">Confirm submission to the external apply flow.</p>
                    <Button variant="primary" fullWidth loading={submitting} onClick={handleSubmit}>
                      Confirm Submit
                    </Button>
                    <Button variant="outline" fullWidth onClick={() => setConfirmSubmit(false)}>
                      Cancel
                    </Button>
                  </div>
                )}
                {!canSubmit && !submitted ? (
                  <p className="text-xs text-muted-foreground">Submission is disabled until readiness, automation, and authorization are complete.</p>
                ) : null}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
};
