"use client";

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';
import { AppShell } from '../components/AppShell';
import { Button, Card, CardContent, CardHeader, CardTitle } from '../components/ui';
import { getStoredAccessToken } from '../../services/auth/auth.service';
import {
  createTailoredResumeForApplication,
  getApplicationById,
  getJobById,
  tailorResumeForApplication,
  type TailoredResumeResultRecord,
  type TailoringRecommendationRecord,
} from '../../services/applications/application-workspace.service';
import { getResumes, type ResumeRead } from '../../services/resumes/resume.service';

export const ApplicationTailorResumePage: React.FC = () => {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const applicationId = String(params?.id || '');
  const token = getStoredAccessToken();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [jobTitle, setJobTitle] = useState<string>('Tailor Resume');
  const [companyName, setCompanyName] = useState<string>('');
  const [jobDescriptionMissing, setJobDescriptionMissing] = useState(false);
  const [customJobDescription, setCustomJobDescription] = useState('');
  const [availableResumes, setAvailableResumes] = useState<ResumeRead[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string>('');
  const [tailoringLoading, setTailoringLoading] = useState(false);
  const [creatingTailoredResume, setCreatingTailoredResume] = useState(false);
  const [tailoringResult, setTailoringResult] = useState<TailoredResumeResultRecord | null>(null);
  const [tailoringError, setTailoringError] = useState<string | null>(null);

  const loadPage = useCallback(async () => {
    if (!token || !applicationId) {
      setError('Please sign in and choose a valid application.');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const [applicationRecord, resumes] = await Promise.all([
        getApplicationById(token, applicationId),
        getResumes(token),
      ]);

      const job = await getJobById(token, applicationRecord.job_id);
      const defaultResume = resumes.find((resume) => resume.id === applicationRecord.resume_id)
        || resumes.find((resume) => resume.is_primary)
        || resumes[0]
        || null;

      setAvailableResumes(resumes);
      setSelectedResumeId(defaultResume?.id || '');
      setJobTitle(job?.title || 'Tailor Resume');
      setCompanyName(job?.company_name || '');
      const hasJobDescription = Boolean(job?.description?.trim());
      setJobDescriptionMissing(!hasJobDescription);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load tailoring page.');
    } finally {
      setLoading(false);
    }
  }, [applicationId, token]);

  useEffect(() => {
    void loadPage();
  }, [loadPage]);

  const groupedTailoringSuggestions = useMemo(() => {
    const suggestions = tailoringResult?.suggestions || [];
    return suggestions.reduce<Record<string, TailoringRecommendationRecord[]>>((acc, suggestion) => {
      const section = (suggestion.section || 'general').toLowerCase();
      if (!acc[section]) {
        acc[section] = [];
      }
      acc[section].push(suggestion);
      return acc;
    }, {});
  }, [tailoringResult]);

  const handleTailorResume = async () => {
    if (!token || !applicationId) return;

    setTailoringLoading(true);
    setTailoringError(null);

    try {
      const trimmedCustomDescription = customJobDescription.trim();
      const result = await tailorResumeForApplication(token, applicationId, {
        resume_id: selectedResumeId || null,
        job_description: jobDescriptionMissing ? (trimmedCustomDescription || null) : null,
      });
      setTailoringResult(result);

      if (result.is_fallback) {
        toast.warning('Tailoring completed with fallback', {
          description: result.message || 'No suggestions were generated.',
        });
      } else {
        toast.success('Resume tailoring complete', {
          description: result.message || 'Suggestions are ready for review.',
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to tailor resume.';
      setTailoringError(message);
      toast.error('Tailor Resume failed', { description: message });
    } finally {
      setTailoringLoading(false);
    }
  };

  const handleCreateTailoredResume = async () => {
    if (!token || !applicationId) return;

    setCreatingTailoredResume(true);
    try {
      const trimmedCustomDescription = customJobDescription.trim();
      const created = await createTailoredResumeForApplication(token, applicationId, {
        resume_id: selectedResumeId || null,
        job_description: jobDescriptionMissing ? (trimmedCustomDescription || null) : null,
      });

      toast.success('Tailored resume saved', {
        description: `${created.file_name} has been saved to your resume library and linked to this application.`,
      });
      router.push('/resumes');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create tailored resume.';
      toast.error('Create tailored resume failed', { description: message });
    } finally {
      setCreatingTailoredResume(false);
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div className="max-w-5xl mx-auto space-y-6 animate-pulse">
          <div className="h-16 rounded-lg bg-muted" />
          <div className="h-64 rounded-lg bg-muted" />
        </div>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell>
        <div className="max-w-4xl mx-auto space-y-4">
          <Button variant="outline" onClick={() => router.push(`/applications/${applicationId}`)}>
            <ArrowLeft className="h-4 w-4" />
            Back to Application
          </Button>
          <Card className="border-destructive/30 bg-destructive/5">
            <CardContent className="pt-6">
              <p className="text-sm text-destructive">{error}</p>
            </CardContent>
          </Card>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="space-y-3">
          <Button variant="outline" onClick={() => router.push(`/applications/${applicationId}`)}>
            <ArrowLeft className="h-4 w-4" />
            Back to Application
          </Button>
          <div>
            <h1 className="text-3xl font-semibold text-foreground">Tailor Resume</h1>
            <p className="mt-2 text-muted-foreground">
              Tailor Resume compares your selected resume against this job description and drafts focused rewrite suggestions you can review before applying.
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              {jobTitle}{companyName ? ` at ${companyName}` : ''}
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Generate Suggestions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {availableResumes.length === 0 ? (
              <div className="rounded-lg border border-warning/30 bg-warning/5 px-3 py-2">
                <p className="text-sm text-warning">No resume available. Upload a resume before generating tailoring suggestions.</p>
              </div>
            ) : (
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Resume</label>
                <select
                  value={selectedResumeId}
                  onChange={(event) => setSelectedResumeId(event.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm hover:bg-accent"
                >
                  {availableResumes.map((resume) => (
                    <option key={resume.id} value={resume.id}>
                      {resume.file_name}{resume.is_primary ? ' (default)' : ''}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {jobDescriptionMissing ? (
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Job Description</label>
                <textarea
                  value={customJobDescription}
                  onChange={(event) => setCustomJobDescription(event.target.value)}
                  rows={8}
                  placeholder="Paste the job description here to generate tailoring suggestions."
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
                <p className="text-xs text-muted-foreground">
                  This field appears only because the original job post is missing a description.
                </p>
              </div>
            ) : null}

            <Button
              onClick={handleTailorResume}
              disabled={
                availableResumes.length === 0
                || tailoringLoading
                || (jobDescriptionMissing && customJobDescription.trim().length === 0)
              }
              loading={tailoringLoading}
            >
              Generate Suggestions
            </Button>

            {tailoringError ? (
              <div className="rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2">
                <p className="text-sm text-destructive">{tailoringError}</p>
              </div>
            ) : null}

            {tailoringResult?.message ? (
              <div
                className={[
                  'rounded-lg border px-3 py-2',
                  tailoringResult.is_fallback
                    ? 'border-warning/30 bg-warning/5'
                    : 'border-success/30 bg-success/5',
                ].join(' ')}
              >
                <p className="text-sm text-muted-foreground">{tailoringResult.message}</p>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recommendations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {tailoringResult && tailoringResult.suggestions.length > 0 && !tailoringResult.is_fallback ? (
              <div className="rounded-lg border border-success/30 bg-success/5 p-3">
                <p className="text-sm text-muted-foreground">
                  Save a tailored resume draft to your account for this application.
                </p>
                <Button
                  className="mt-3"
                  onClick={handleCreateTailoredResume}
                  loading={creatingTailoredResume}
                  disabled={creatingTailoredResume}
                >
                  Create Tailored Resume
                </Button>
              </div>
            ) : null}

            {tailoringResult && tailoringResult.suggestions.length === 0 && !tailoringError ? (
              <p className="text-sm text-muted-foreground">No tailoring suggestions were returned for this context.</p>
            ) : null}

            {!tailoringResult && !tailoringError ? (
              <p className="text-sm text-muted-foreground">Generate suggestions to review targeted rewrite recommendations by resume section.</p>
            ) : null}

            {Object.entries(groupedTailoringSuggestions).map(([section, suggestions]) => (
              <div key={section} className="space-y-3 rounded-lg border border-border p-3">
                <p className="text-sm font-medium capitalize text-foreground">{section}</p>
                {suggestions.map((suggestion, index) => (
                  <div key={`${section}-${index}`} className="space-y-2 rounded-md border border-border p-3">
                    {suggestion.current_text ? (
                      <div>
                        <p className="text-xs font-medium text-muted-foreground">Current</p>
                        <p className="whitespace-pre-wrap text-sm text-muted-foreground">{suggestion.current_text}</p>
                      </div>
                    ) : null}
                    <div>
                      <p className="text-xs font-medium text-foreground">Proposed</p>
                      <p className="whitespace-pre-wrap text-sm text-foreground">{suggestion.proposed_text}</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-muted-foreground">Reason</p>
                      <p className="text-sm text-muted-foreground">{suggestion.reason}</p>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
};