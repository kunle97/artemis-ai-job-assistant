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
  Edit3,
  ExternalLink,
  Play,
  RefreshCw,
  Send,
  Shield,
  Wand2,
} from 'lucide-react';
import { getStoredAccessToken } from '../../services/auth/auth.service';
import {
  authorizeApplication,
  buildAutomationFillPlan,
  getApplicationById,
  getApplicationReadiness,
  getApplicationStatus,
  getJobById,
  inspectApplicationPage,
  runApplicationPipeline,
  submitApplication,
  updateLifecycleStatus,
  type AutomationInspectedField,
  type AutomationPlannedFieldRecord,
  type ApplicationReadinessRecord,
  type ApplicationRecord,
  type ApplicationStatusRecord,
} from '../../services/applications/application-workspace.service';
import {
  buildApplicationAnswerQuestionKey,
  generateApplicationAnswer,
  resolveApplicationAnswer,
  saveApplicationAnswer,
} from '../../services/applications/application-answers.service';

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

interface AutofillPreviewItem {
  key: string;
  questionText: string;
  resolvedValue: string;
  source: string;
  needsReview: boolean;
  fieldType: string;
  inputSubtype: string | null;
  options: string[];
}

// Bump this when preview extraction changes so stale sessionStorage entries do not hide new fields.
const AUTOFILL_PREVIEW_CACHE_PREFIX = 'autofill-preview-cache:v3';

interface AutofillPreviewCacheEntry {
  applicationUpdatedAt: string;
  items: AutofillPreviewItem[];
}

function extractOptionValues(rawOptions: Array<Record<string, unknown>>): string[] {
  const values = rawOptions
    .map((option) => {
      const value = option.value ?? option.label ?? option.text ?? option.name;
      return typeof value === 'string' ? value.trim() : '';
    })
    .filter((value) => value.length > 0);

  return Array.from(new Set(values));
}

function parseMultiValueSelection(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function toggleMultiValueSelection(currentValue: string, option: string, checked: boolean): string {
  const selections = new Set(parseMultiValueSelection(currentValue));
  if (checked) {
    selections.add(option);
  } else {
    selections.delete(option);
  }
  return Array.from(selections).join(', ');
}

function isBinaryYesNoField(item: AutofillPreviewItem): boolean {
  const optionList = Array.isArray(item.options) ? item.options : [];
  const normalizedOptions = optionList.map((option) => option.trim().toLowerCase());
  const hasYes = normalizedOptions.includes('yes');
  const hasNo = normalizedOptions.includes('no');
  if (hasYes && hasNo) return true;

  if (item.fieldType === 'radio_group' && optionList.length === 0) {
    return true;
  }

  if (['work_authorization', 'relocation', 'consent_question', 'compliance_question'].includes(item.source)) {
    return true;
  }

  const loweredQuestion = item.questionText.trim().toLowerCase();
  return (
    loweredQuestion.startsWith('are you')
    || loweredQuestion.startsWith('do you')
    || loweredQuestion.startsWith('will you')
    || loweredQuestion.startsWith('can you')
  );
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
  const [autofillPreview, setAutofillPreview] = useState<AutofillPreviewItem[]>([]);
  const [autofillPreviewLoading, setAutofillPreviewLoading] = useState(false);
  const [autofillPreviewNote, setAutofillPreviewNote] = useState<string | null>(null);
  const [editingFieldKey, setEditingFieldKey] = useState<string | null>(null);
  const [editingValue, setEditingValue] = useState('');
  const [savingFieldKey, setSavingFieldKey] = useState<string | null>(null);
  const [textareaOverrideKey, setTextareaOverrideKey] = useState<string | null>(null);
  const [generatingFieldKey, setGeneratingFieldKey] = useState<string | null>(null);

  const [automationState, setAutomationState] = useState<AutomationState>('idle');
  const [runTaskId, setRunTaskId] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  const [running, setRunning] = useState(false);
  const [authorizing, setAuthorizing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [confirmSubmit, setConfirmSubmit] = useState(false);
  const [updatingLifecycleStatus, setUpdatingLifecycleStatus] = useState(false);

  const getPreviewCacheKey = (id: string) => `${AUTOFILL_PREVIEW_CACHE_PREFIX}:${id}`;

  const readCachedAutofillPreview = useCallback(
    (applicationUpdatedAt: string): AutofillPreviewItem[] | null => {
      if (typeof window === 'undefined') return null;
      const raw = window.sessionStorage.getItem(getPreviewCacheKey(applicationId));
      if (!raw) return null;

      try {
        const parsed = JSON.parse(raw) as AutofillPreviewCacheEntry;
        if (parsed.applicationUpdatedAt !== applicationUpdatedAt) return null;
        return (parsed.items || []).map((item) => ({
          key: item.key,
          questionText: item.questionText,
          resolvedValue: item.resolvedValue || '',
          source: item.source || 'unknown',
          needsReview: Boolean(item.needsReview),
          fieldType: item.fieldType || 'input',
          inputSubtype: item.inputSubtype ?? null,
          options: Array.isArray(item.options) ? item.options : [],
        }));
      } catch {
        return null;
      }
    },
    [applicationId],
  );

  const writeCachedAutofillPreview = useCallback(
    (applicationUpdatedAt: string, items: AutofillPreviewItem[]) => {
      if (typeof window === 'undefined') return;
      const cacheEntry: AutofillPreviewCacheEntry = {
        applicationUpdatedAt,
        items,
      };
      window.sessionStorage.setItem(getPreviewCacheKey(applicationId), JSON.stringify(cacheEntry));
    },
    [applicationId],
  );

  const buildAutofillPreviewItems = (fields: AutomationPlannedFieldRecord[]): AutofillPreviewItem[] => {
    const previewableFields = fields.filter((field) => {
      const role = (field.classified_role || '').trim().toLowerCase();
      if (['ignore', 'submit_action'].includes(role)) return false;
      return true;
    });

    return previewableFields.map((field, index) => ({
      key: [field.classified_role, field.name, field.label, field.placeholder, String(index)]
        .filter((part): part is string => Boolean(part && part.trim().length > 0))
        .join('|'),
      questionText: field.label?.trim() || field.name?.trim() || field.placeholder?.trim() || 'Application field',
      resolvedValue: field.resolved_value ? String(field.resolved_value) : '',
      source: field.classified_role,
      needsReview: field.needs_review,
      fieldType: field.field_type,
      inputSubtype: field.input_subtype,
      options: extractOptionValues(field.options || []),
    }));
  };

  const buildPreviewFallbackFromInspection = (fields: AutomationInspectedField[]): AutofillPreviewItem[] => {
    return fields.map((field, index) => ({
      key: ['inspection', field.field_type, field.name, field.label, field.placeholder, String(index)]
        .filter((part): part is string => Boolean(part && part.trim().length > 0))
        .join('|'),
      questionText: field.label?.trim() || field.name?.trim() || field.placeholder?.trim() || 'Application field',
      resolvedValue: '',
      source: 'unclassified',
      needsReview: true,
      fieldType: field.field_type || 'input',
      inputSubtype: field.input_subtype ?? null,
      options: [],
    }));
  };

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

        if (job.apply_url) {
          const cachedPreview = readCachedAutofillPreview(applicationRecord.updated_at);
          if (cachedPreview) {
            setAutofillPreview(cachedPreview);
            setAutofillPreviewNote(null);
          } else {
            setAutofillPreviewLoading(true);
            try {
              const inspection = await inspectApplicationPage(token, job.apply_url);
              let previewItems: AutofillPreviewItem[] = [];
              let previewNote: string | null = null;

              try {
                const plan = await buildAutomationFillPlan(token, {
                  application_url: job.apply_url,
                  inspected_fields: inspection.fields,
                  page_title: inspection.title,
                  job_context: inspection.job_context,
                });
                previewItems = buildAutofillPreviewItems(plan.fields);

                if (previewItems.length === 0 && inspection.fields.length > 0) {
                  previewItems = buildPreviewFallbackFromInspection(inspection.fields);
                  previewNote = `Preview fallback mode: detected ${inspection.fields.length} raw fields but planning returned none.`;
                } else if (inspection.fields.length > previewItems.length) {
                  previewNote = `Detected ${inspection.fields.length} raw fields; previewing ${previewItems.length} planned fields.`;
                }
              } catch {
                previewItems = buildPreviewFallbackFromInspection(inspection.fields);
                previewNote = inspection.fields.length > 0
                  ? `Planning failed; showing ${inspection.fields.length} detected fields for review.`
                  : 'Planning failed and no detectable fields were returned by inspection.';
              }

              setAutofillPreview(previewItems);
              setAutofillPreviewNote(previewNote);
              writeCachedAutofillPreview(applicationRecord.updated_at, previewItems);
            } catch {
              setAutofillPreview([]);
              setAutofillPreviewNote('Could not inspect this form for preview. Try rerunning automation.');
            } finally {
              setAutofillPreviewLoading(false);
            }
          }
        } else {
          setAutofillPreview([]);
          setAutofillPreviewNote(null);
        }
      } else {
        setJobTitle('Application');
        setCompanyName('Unknown company');
        setLocationLabel('Unknown location');
        setWorkModeLabel('Unknown work mode');
        setJobUrl(null);
        setAutofillPreview([]);
        setAutofillPreviewNote(null);
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
  }, [applicationId, readCachedAutofillPreview, token, writeCachedAutofillPreview]);

  const handleStartInlineEdit = (item: AutofillPreviewItem) => {
    setEditingFieldKey(item.key);
    setTextareaOverrideKey(null);
    if (item.fieldType === 'checkbox_group') {
      setEditingValue('');
      return;
    }

    setEditingValue(item.resolvedValue);
  };

  const handleCancelInlineEdit = () => {
    setEditingFieldKey(null);
    setEditingValue('');
    setTextareaOverrideKey(null);
  };

  const handleSaveInlineEdit = async (item: AutofillPreviewItem) => {
    const normalizedAnswer = editingValue.trim();
    if (!token || !normalizedAnswer) return;

    setSavingFieldKey(item.key);
    try {
      await saveApplicationAnswer(token, {
        question_key: buildApplicationAnswerQuestionKey(item.questionText),
        question_text: item.questionText,
        answer_text: normalizedAnswer,
      });

      setAutofillPreview((prev) => {
        const next = prev.map((candidate) => (
          candidate.key === item.key
            ? {
              ...candidate,
              resolvedValue: normalizedAnswer,
              needsReview: false,
            }
            : candidate
        ));
        if (application?.updated_at) {
          writeCachedAutofillPreview(application.updated_at, next);
        }
        return next;
      });

      setEditingFieldKey(null);
      setEditingValue('');
      toast.success('Answer updated', {
        description: 'Your edited answer was saved to the reusable answer library.',
      });
    } catch (inlineEditError) {
      const message = inlineEditError instanceof Error ? inlineEditError.message : 'Failed to save answer.';
      toast.error('Save failed', { description: message });
    } finally {
      setSavingFieldKey(null);
    }
  };

  const handleGenerateAnswer = async (item: AutofillPreviewItem) => {
    if (!token) {
      toast.error('Not signed in', {
        description: 'Please sign in again to generate answers.',
      });
      return;
    }

    setGeneratingFieldKey(item.key);
    try {
      const resolution = await resolveApplicationAnswer(token, item.questionText);
      let generated = (resolution.resolved_answer || '').trim();
      let generatedSource = resolution.source || item.source;
      let generatedNeedsReview = Boolean(resolution.needs_review);

      if (!generated && (resolution.source || 'unresolved') === 'unresolved') {
        const generation = await generateApplicationAnswer(token, {
          questionText: item.questionText,
          pageTitle: jobTitle,
          jobContext: [companyName, locationLabel, workModeLabel]
            .filter((part) => part && !part.toLowerCase().startsWith('unknown'))
            .join(' | '),
        });
        generated = (generation.answer_text || '').trim();
        generatedSource = generation.source || generatedSource;
        generatedNeedsReview = Boolean(generation.needs_review);
      }

      if (!generated) {
        const fallback = (item.resolvedValue || '').trim();
        if (fallback) {
          setEditingFieldKey(item.key);
          setTextareaOverrideKey(null);
          setEditingValue(fallback);
          toast.success('Using existing suggestion', {
            description: 'No new generated answer yet, so Artemis loaded the current autofill suggestion.',
          });
          return;
        }

        setEditingFieldKey(item.key);
        setTextareaOverrideKey(item.fieldType === 'textarea' ? item.key : null);
        setEditingValue('');

        toast.error('No generated answer', {
          description: `No answer available yet (source: ${generatedSource || 'unresolved'}). Enter one manually and save it for reuse.`,
        });
        return;
      }

      setAutofillPreview((prev) => {
        const next = prev.map((candidate) => (
          candidate.key === item.key
            ? {
              ...candidate,
              resolvedValue: generated,
              source: generatedSource || candidate.source,
              needsReview: generatedNeedsReview,
            }
            : candidate
        ));
        if (application?.updated_at) {
          writeCachedAutofillPreview(application.updated_at, next);
        }
        return next;
      });

      setEditingFieldKey(item.key);
      setTextareaOverrideKey(null);
      setEditingValue(generated);

      toast.success('Answer generated', {
        description: `Review and save the generated answer if it looks right (source: ${generatedSource}).`,
      });
    } catch (generateError) {
      const message = generateError instanceof Error ? generateError.message : 'Failed to generate answer.';
      toast.error('Generation failed', { description: message });
    } finally {
      setGeneratingFieldKey(null);
    }
  };

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

  const handleUpdateLifecycleStatus = async (newStatus: string) => {
    if (!token || !applicationId) return;
    setUpdatingLifecycleStatus(true);
    try {
      await updateLifecycleStatus(token, applicationId, newStatus);
      toast.success('Status updated', { description: `Application marked as ${newStatus}.` });
      await loadWorkspace();
    } catch (err) {
      toast.error('Failed to update status', {
        description: err instanceof Error ? err.message : 'An unexpected error occurred.',
      });
    } finally {
      setUpdatingLifecycleStatus(false);
    }
  };

  const handleRunAutomation = async () => {    if (!token || !applicationId) return;
    setRunning(true);
    setRunError(null);
    setAutomationState('queued');

    try {
      const dispatch = await runApplicationPipeline(token, applicationId);
      setRunTaskId(dispatch.task_id);
      const dispatchedState: AutomationState = dispatch.status === 'queued' ? 'queued' : 'running';
      setAutomationState(dispatchedState);
      toast.success('Automation queued', {
        description: 'The automation pipeline has been dispatched.',
      });
      await loadWorkspace();
      // Re-assert the active state if loadWorkspace() got a stale server
      // response and reset automationState back to 'idle' before the worker
      // has had a chance to update the status record.
      setAutomationState((current) => (current === 'idle' ? dispatchedState : current));
    } catch (runPipelineError) {
      const errMsg = runPipelineError instanceof Error ? runPipelineError.message : 'Automation dispatch failed.';
      setRunError(errMsg);
      setAutomationState('failure');
      toast.error('Automation failed', { description: errMsg });
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

            <Card>
              <CardHeader>
                <CardTitle>Autofilled Fields Preview</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {autofillPreviewNote ? (
                  <div className="rounded-lg border border-warning/30 bg-warning/5 px-3 py-2">
                    <p className="text-xs text-warning">{autofillPreviewNote}</p>
                  </div>
                ) : null}
                {autofillPreviewLoading ? (
                  <p className="text-sm text-muted-foreground">Loading autofill preview...</p>
                ) : autofillPreview.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No autofilled fields available yet. Run automation to generate a preview.</p>
                ) : (
                  <div className="space-y-3">
                    {autofillPreview.map((item) => (
                      <div key={item.key} className="rounded-lg border border-border p-3">
                        <div className="flex items-start justify-between gap-3">
                          <p className="text-sm font-medium text-foreground">{item.questionText}</p>
                          <div className="flex items-center gap-2">
                            {!submitted && ['input', 'textarea'].includes(item.fieldType) ? (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => void handleGenerateAnswer(item)}
                                loading={generatingFieldKey === item.key}
                              >
                                <Wand2 className="h-3.5 w-3.5" />
                                Generate Answer
                              </Button>
                            ) : null}
                            {item.needsReview ? (
                              <Badge variant="warning" size="sm">Needs review</Badge>
                            ) : (
                              <Badge variant="success" size="sm">Autofilled</Badge>
                            )}
                            {!submitted ? (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleStartInlineEdit(item)}
                              >
                                <Edit3 className="h-3.5 w-3.5" />
                                Edit
                              </Button>
                            ) : null}
                          </div>
                        </div>
                        {editingFieldKey === item.key ? (
                          <div className="mt-2 space-y-2">
                            {(() => {
                              const isChoiceField = ['select', 'select_like', 'radio_group'].includes(item.fieldType);
                              const isCheckboxGroupField = item.fieldType === 'checkbox_group';
                              const isDateField = item.inputSubtype === 'date' || item.source === 'desired_start_date';
                              const isYesNoField = isBinaryYesNoField(item);
                              const itemOptions = Array.isArray(item.options) ? item.options : [];
                              const isTextareaMode = item.fieldType === 'textarea' || textareaOverrideKey === item.key;

                              if (isYesNoField) {
                                return (
                                  <>
                                    {!isTextareaMode ? (
                                      <div className="flex items-center gap-4">
                                        {['Yes', 'No'].map((option) => (
                                          <label key={option} className="inline-flex items-center gap-2 text-sm text-foreground">
                                            <input
                                              type="radio"
                                              name={`preview-binary-${item.key}`}
                                              value={option}
                                              checked={editingValue.trim().toLowerCase() === option.toLowerCase()}
                                              onChange={(event) => setEditingValue(event.target.value)}
                                              className="h-4 w-4 border-border text-brand"
                                            />
                                            {option}
                                          </label>
                                        ))}
                                      </div>
                                    ) : (
                                      <textarea
                                        value={editingValue}
                                        onChange={(event) => setEditingValue(event.target.value)}
                                        rows={4}
                                        className="w-full px-3 py-2 rounded-lg border border-border bg-input-background focus:ring-2 focus:ring-brand focus:border-brand resize-y"
                                        placeholder="Type your custom response here..."
                                      />
                                    )}
                                  </>
                                );
                              }

                              if (isChoiceField && itemOptions.length > 0) {
                                const selectionOptions = itemOptions.includes(editingValue)
                                  ? itemOptions
                                  : [editingValue, ...itemOptions].filter((option) => option.trim().length > 0);

                                return (
                                  <select
                                    value={editingValue}
                                    onChange={(event) => setEditingValue(event.target.value)}
                                    className="w-full px-3 py-2 rounded-lg border border-border bg-input-background focus:ring-2 focus:ring-brand focus:border-brand"
                                  >
                                    {selectionOptions.map((option) => (
                                      <option key={option} value={option}>{option}</option>
                                    ))}
                                  </select>
                                );
                              }

                              if (isCheckboxGroupField && itemOptions.length > 0) {
                                const selectedOptions = new Set(parseMultiValueSelection(editingValue));

                                return (
                                  <div className="space-y-2">
                                    <p className="text-xs text-muted-foreground">Select all options that apply.</p>
                                    <div className="space-y-2 rounded-lg border border-border bg-secondary/20 p-3">
                                      {itemOptions.map((option) => (
                                        <label key={option} className="flex items-center gap-2 text-sm text-foreground">
                                          <input
                                            type="checkbox"
                                            checked={selectedOptions.has(option)}
                                            onChange={(event) => setEditingValue(
                                              toggleMultiValueSelection(editingValue, option, event.target.checked),
                                            )}
                                            className="h-4 w-4 rounded border-border text-brand"
                                          />
                                          <span>{option}</span>
                                        </label>
                                      ))}
                                    </div>
                                  </div>
                                );
                              }

                              if (isDateField) {
                                return (
                                  <input
                                    type="date"
                                    value={editingValue}
                                    onChange={(event) => setEditingValue(event.target.value)}
                                    className="w-full px-3 py-2 rounded-lg border border-border bg-input-background focus:ring-2 focus:ring-brand focus:border-brand"
                                  />
                                );
                              }

                              if (item.fieldType === 'textarea') {
                                return (
                                  <textarea
                                    value={editingValue}
                                    onChange={(event) => setEditingValue(event.target.value)}
                                    rows={4}
                                    className="w-full px-3 py-2 rounded-lg border border-border bg-input-background focus:ring-2 focus:ring-brand focus:border-brand resize-y"
                                  />
                                );
                              }

                              return (
                                <input
                                  type="text"
                                  value={editingValue}
                                  onChange={(event) => setEditingValue(event.target.value)}
                                  className="w-full px-3 py-2 rounded-lg border border-border bg-input-background focus:ring-2 focus:ring-brand focus:border-brand"
                                />
                              );
                            })()}
                            <div className="flex items-center gap-2">
                              {isBinaryYesNoField(item) ? (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => {
                                    setTextareaOverrideKey((current) => (current === item.key ? null : item.key));
                                  }}
                                >
                                  {textareaOverrideKey === item.key ? 'Use Yes/No' : 'Switch to textarea'}
                                </Button>
                              ) : null}
                              <Button
                                size="sm"
                                onClick={() => void handleSaveInlineEdit(item)}
                                loading={savingFieldKey === item.key}
                                disabled={editingValue.trim().length === 0}
                              >
                                Save
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={handleCancelInlineEdit}
                                disabled={savingFieldKey === item.key}
                              >
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div className="mt-2 space-y-2">
                            <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                              {item.resolvedValue || 'No autofill value yet.'}
                            </p>
                            {item.fieldType === 'checkbox_group' && item.options.length > 0 ? (
                              <div className="rounded-lg border border-border bg-secondary/20 p-3">
                                <p className="text-xs font-medium text-foreground">Available options</p>
                                <div className="mt-2 flex flex-wrap gap-2">
                                  {item.options.map((option) => {
                                    const isSelected = parseMultiValueSelection(item.resolvedValue).includes(option);
                                    return (
                                      <span
                                        key={option}
                                        className={[
                                          'inline-flex items-center rounded-full border px-2.5 py-1 text-xs',
                                          isSelected
                                            ? 'border-brand/40 bg-brand/10 text-foreground'
                                            : 'border-border bg-background text-muted-foreground',
                                        ].join(' ')}
                                      >
                                        {option}
                                      </span>
                                    );
                                  })}
                                </div>
                              </div>
                            ) : null}
                          </div>
                        )}
                        <p className="mt-2 text-xs text-muted-foreground">Source: {item.source}</p>
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
                <CardTitle>Tailor Resume</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Tailor Resume compares your resume against this job and generates focused rewrite suggestions on a dedicated review page.
                </p>

                <Button
                  onClick={() => router.push(`/applications/${applicationId}/tailor-resume`)}
                >
                  Open Tailor Resume
                </Button>
              </CardContent>
            </Card>

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

            {['submitted', 'interviewing', 'offer_received', 'offer_accepted', 'rejected'].includes(normalizedStatus) && (
              <Card className="border-blue/30 bg-blue/5">
                <CardHeader>
                  <CardTitle>Application Status</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-xs text-muted-foreground">Track the status of your application throughout the hiring process.</p>
                  <select
                    value={normalizedStatus}
                    onChange={(e) => handleUpdateLifecycleStatus(e.target.value)}
                    disabled={updatingLifecycleStatus}
                    className="w-full px-3 py-2 text-sm border border-input rounded-md bg-background hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <option value="submitted">Submitted</option>
                    <option value="interviewing">Interviewing</option>
                    <option value="offer_received">Offer Received</option>
                    <option value="offer_accepted">Offer Accepted</option>
                    <option value="rejected">Rejected</option>
                    <option value="archived">Archived</option>
                  </select>
                </CardContent>
              </Card>
            )}

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
                    <div className="flex items-center gap-2">
                      <Button variant="outline" fullWidth onClick={() => setConfirmSubmit(false)}>
                        Cancel
                      </Button>
                    </div>
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
