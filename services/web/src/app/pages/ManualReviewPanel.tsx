'use client';
import React, { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { AppShell } from '../components/AppShell';
import { Button, Card, Badge } from '../components/ui';
import { ArrowLeft, Save, AlertCircle, CheckCircle, RefreshCw, Sparkles, ExternalLink } from 'lucide-react';
import { getStoredAccessToken } from '../../services/auth/auth.service';
import {
  buildAutomationFillPlan,
  getApplicationById,
  getApplicationStatus,
  getJobById,
  inspectApplicationPage,
  runApplicationPipeline,
  type AutomationPlannedFieldRecord,
} from '../../services/applications/application-workspace.service';
import {
  saveApplicationAnswer,
  buildApplicationAnswerQuestionKey,
} from '../../services/applications/application-answers.service';

interface ReviewField {
  fieldKey: string;
  questionText: string;
  suggestedAnswer: string | null;
  source: string;
  needsReview: boolean;
  userAnswer: string;
  saved: boolean;
}

function toReviewField(item: AutomationPlannedFieldRecord): ReviewField {
  const questionText = item.label?.trim() || item.name?.trim() || item.placeholder?.trim() || 'Application field';
  const stableFieldKey = [item.classified_role, item.name, item.label, item.placeholder]
    .filter((part): part is string => Boolean(part && part.trim().length > 0))
    .join('|') || 'application-field';
  return {
    fieldKey: stableFieldKey,
    questionText,
    suggestedAnswer: item.resolved_value,
    source: item.classified_role,
    needsReview: item.needs_review,
    userAnswer: item.resolved_value ?? '',
    saved: false,
  };
}

function shouldIncludeField(item: AutomationPlannedFieldRecord): boolean {
  if (['ignore', 'submit_action', 'resume_upload', 'cover_letter_upload'].includes(item.classified_role)) {
    return false;
  }
  if (item.classified_role === 'open_ended_question') {
    return true;
  }
  // Always surface if the system could not resolve a value — regardless of
  // whether the form marked the field as required (some ATS forms omit the
  // required attribute while still expecting an answer).
  if (item.needs_review) return true;
  // Also show required fields that have no resolved value yet.
  return item.required && !item.resolved_value;
}

export const ManualReviewPanel: React.FC = () => {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const applicationId = String(params?.id || '');
  const token = getStoredAccessToken();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<ReviewField[]>([]);
  const [manualReviewRequired, setManualReviewRequired] = useState(false);
  const [jobTitle, setJobTitle] = useState<string>('Application');
  const [companyName, setCompanyName] = useState<string>('');
  const [jobUrl, setJobUrl] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [continuing, setContinuing] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const loadReviewData = useCallback(async () => {
    if (!token || !applicationId) {
      setError('Please sign in and choose a valid application.');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const [applicationRecord, statusRecord] = await Promise.all([
        getApplicationById(token, applicationId),
        getApplicationStatus(token, applicationId),
      ]);
      setManualReviewRequired(statusRecord.manual_review_required);

      const job = await getJobById(token, applicationRecord.job_id);
      if (job) {
        setJobTitle(job.title || 'Application');
        setCompanyName(job.company_name || '');
        setJobUrl(job.apply_url || null);
      } else {
        setJobUrl(null);
      }

      if (!job?.apply_url) {
        setFields([]);
        return;
      }

      const inspection = await inspectApplicationPage(token, job.apply_url);
      const plan = await buildAutomationFillPlan(token, {
        application_url: job.apply_url,
        inspected_fields: inspection.fields,
        page_title: inspection.title,
        job_context: inspection.job_context,
      });

      const reviewItems = plan.fields.filter(shouldIncludeField);
      setFields(reviewItems.map(toReviewField));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load review data.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [applicationId, token]);

  useEffect(() => {
    void loadReviewData();
  }, [loadReviewData]);

  const handleFieldChange = (fieldKey: string, value: string) => {
    setFields((prev) =>
      prev.map((f) => (f.fieldKey === fieldKey ? { ...f, userAnswer: value, saved: false } : f)),
    );
  };

  const handleUseSuggestion = (fieldKey: string) => {
    setFields((prev) =>
      prev.map((f) =>
        f.fieldKey === fieldKey && f.suggestedAnswer
          ? { ...f, userAnswer: f.suggestedAnswer, saved: false }
          : f,
      ),
    );
  };

  const handleSave = async () => {
    if (!token) return;
    setSaving(true);
    setSaveError(null);

    try {
      const filledFields = fields.filter((f) => f.userAnswer.trim().length > 0);
      const savedAnswers = await Promise.all(
        filledFields.map((f) =>
          saveApplicationAnswer(token, {
            question_key: buildApplicationAnswerQuestionKey(f.questionText),
            question_text: f.questionText,
            answer_text: f.userAnswer.trim(),
          }),
        ),
      );

      const allSaved = savedAnswers.every((answer) => Boolean(answer?.id));
      if (!allSaved) {
        throw new Error('Some reviewed fields were not saved to your question library. Please try again.');
      }

      setFields((prev) =>
        prev.map((f) => (f.userAnswer.trim().length > 0 ? { ...f, saved: true } : f)),
      );

      // Re-dispatch automation so newly reviewed answers are applied.
      await runApplicationPipeline(token, applicationId);

      router.push(`/applications/${applicationId}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save answers.';
      setSaveError(message);
    } finally {
      setSaving(false);
    }
  };

  const handleContinueWithoutSaving = async () => {
    if (!token) return;
    setContinuing(true);
    setSaveError(null);

    try {
      await runApplicationPipeline(token, applicationId);
      router.push(`/applications/${applicationId}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to re-run automation.';
      setSaveError(message);
    } finally {
      setContinuing(false);
    }
  };

  const filledFields = fields.filter((f) => f.userAnswer.trim().length > 0).length;
  const totalFields = fields.length;

  if (loading) {
    return (
      <AppShell>
        <div className="max-w-5xl mx-auto space-y-6 animate-pulse">
          <div className="h-20 rounded-lg bg-muted" />
          <div className="h-64 rounded-lg bg-muted" />
        </div>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell>
        <div className="max-w-5xl mx-auto space-y-4">
          <Button variant="outline" onClick={() => router.push(`/applications/${applicationId}`)}>
            <ArrowLeft className="h-4 w-4" />
            Back to Application
          </Button>
          <Card className="border-destructive/30 bg-destructive/5">
            <div className="p-4 space-y-3">
              <p className="text-sm text-destructive">{error}</p>
              <Button variant="outline" onClick={() => void loadReviewData()}>
                <RefreshCw className="h-4 w-4" />
                Retry
              </Button>
            </div>
          </Card>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto">
        <div className="mb-6">
          <button
            onClick={() => router.push(`/applications/${applicationId}`)}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-4"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Application
          </button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-semibold text-foreground">Manual Review Required</h1>
              {(jobTitle || companyName) && (
                <p className="mt-1 text-muted-foreground">
                  {jobTitle}{companyName ? ` at ${companyName}` : ''}
                </p>
              )}
              {jobUrl && (
                <a
                  href={jobUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-flex items-center gap-1 text-sm text-brand hover:underline"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  Open live application page
                </a>
              )}
            </div>
            {totalFields > 0 && (
              <Badge variant={filledFields === totalFields ? 'success' : 'warning'}>
                {filledFields} of {totalFields} resolved
              </Badge>
            )}
          </div>
        </div>

        {fields.length === 0 ? (
          <Card>
            <div className="p-6 space-y-2">
              <p className="text-sm font-medium text-foreground">
                {manualReviewRequired ? 'No review fields are available yet' : 'No fields need manual review'}
              </p>
              <p className="text-sm text-muted-foreground">
                {manualReviewRequired
                  ? 'No unresolved fields were found from the latest form inspection. Re-run automation if the external form changed.'
                  : 'All fields were filled with high confidence. You can proceed to authorization.'}
              </p>
              <Button
                variant="outline"
                className="mt-3"
                onClick={() => router.push(`/applications/${applicationId}`)}
              >
                Back to Application
              </Button>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Card variant="outlined" className="bg-info/5 border-info/20">
                <div className="flex gap-3 p-4">
                  <AlertCircle className="h-5 w-5 text-info flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-foreground mb-1">
                      These fields need your attention
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Artemis couldn't fill these fields with high confidence. Review or correct
                      each answer before authorizing submission.
                    </p>
                  </div>
                </div>
              </Card>

              <div className="space-y-6">
                {fields.map((field) => (
                  <Card key={field.fieldKey} padding="md" variant="outlined">
                    <div className="space-y-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h3 className="font-semibold text-foreground">{field.questionText}</h3>
                          <p className="text-xs text-muted-foreground mt-1">
                            Source: {field.source}
                            {field.needsReview && (
                              <span className="ml-2 text-warning font-medium">· Low confidence</span>
                            )}
                            {!field.suggestedAnswer && (
                              <span className="ml-2 text-destructive font-medium">· Not resolved</span>
                            )}
                          </p>
                        </div>
                        {field.saved && (
                          <div className="flex items-center gap-1 text-success text-xs whitespace-nowrap">
                            <CheckCircle className="h-4 w-4" />
                            Saved
                          </div>
                        )}
                      </div>

                      {field.suggestedAnswer && (
                        <div className="p-3 rounded-lg bg-brand/5 border border-brand/20">
                          <div className="flex items-start gap-2 mb-2">
                            <Sparkles className="h-4 w-4 text-brand flex-shrink-0 mt-0.5" />
                            <p className="text-sm font-medium text-foreground">Suggested Answer</p>
                          </div>
                          <p className="text-sm text-muted-foreground mb-3">{field.suggestedAnswer}</p>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleUseSuggestion(field.fieldKey)}
                          >
                            Use This Answer
                          </Button>
                        </div>
                      )}

                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Your Answer
                        </label>
                        <textarea
                          value={field.userAnswer}
                          onChange={(e) => handleFieldChange(field.fieldKey, e.target.value)}
                          placeholder="Enter your answer here..."
                          rows={4}
                          className="w-full px-4 py-2 rounded-lg border border-border bg-input-background focus:ring-2 focus:ring-brand focus:border-brand resize-y"
                        />
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>

            <div className="space-y-6">
              <Card>
                <div className="p-4 space-y-4">
                  <div>
                    <h3 className="font-semibold text-foreground mb-2">Progress</h3>
                    <div className="flex items-center gap-3">
                      <div className="flex-1 h-3 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-brand transition-all duration-300"
                          style={{ width: `${totalFields > 0 ? (filledFields / totalFields) * 100 : 0}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-foreground">
                        {totalFields > 0 ? Math.round((filledFields / totalFields) * 100) : 0}%
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2 pt-4 border-t border-border">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Total fields</span>
                      <span className="font-medium text-foreground">{totalFields}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Resolved</span>
                      <span className="font-medium text-foreground">{filledFields}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Remaining</span>
                      <span className="font-medium text-foreground">{totalFields - filledFields}</span>
                    </div>
                  </div>
                </div>
              </Card>

              <Card>
                <div className="p-4 space-y-3">
                  <h3 className="font-semibold text-foreground mb-2">Actions</h3>
                  {saveError && (
                    <p className="text-xs text-destructive">{saveError}</p>
                  )}
                  <Button
                    variant="primary"
                    fullWidth
                    onClick={handleSave}
                    loading={saving}
                    disabled={saving || filledFields === 0}
                  >
                    <Save className="h-4 w-4" />
                    Save & Continue
                  </Button>
                  <Button
                    variant="outline"
                    fullWidth
                    onClick={() => void handleContinueWithoutSaving()}
                    loading={continuing}
                    disabled={saving || continuing}
                  >
                    Continue Without Saving
                  </Button>
                </div>
              </Card>

              <Card variant="outlined" className="bg-muted/30">
                <div className="p-4">
                  <h3 className="font-semibold text-foreground mb-3">Tips</h3>
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    <li className="flex gap-2">
                      <span>•</span>
                      <span>Use suggested answers as a starting point and customize them</span>
                    </li>
                    <li className="flex gap-2">
                      <span>•</span>
                      <span>Saved answers are added to your library for future applications</span>
                    </li>
                    <li className="flex gap-2">
                      <span>•</span>
                      <span>You can re-run automation after saving to update filled fields</span>
                    </li>
                  </ul>
                </div>
              </Card>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
};
