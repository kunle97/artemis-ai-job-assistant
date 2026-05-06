'use client';

import React, { useRef, useState } from 'react';
import { Button, Input, Card } from './ui';
import {
  uploadResume,
  type ResumeNormalizedData,
} from '../../services/resumes/resume.service';
import {
  Sparkles,
  CheckCircle,
  Upload,
  User,
  Briefcase,
  Zap,
  ArrowRight,
  ArrowLeft,
  Loader2,
} from 'lucide-react';

type SetupStep = 'profile' | 'resume' | 'preferences';
type OnboardingStep = SetupStep | 'complete';
type OnboardingStepStatus = 'pending' | 'completed' | 'skipped';
type OnboardingStatus = Record<SetupStep, OnboardingStepStatus>;

interface RegistrationOnboardingProps {
  firstName?: string;
  onComplete: () => void;
}

const inferWorkStyle = (text: string | null | undefined): string[] => {
  const lower = (text ?? '').toLowerCase();
  if (lower.includes('hybrid')) return ['Hybrid'];
  if (lower.includes('remote')) return ['Remote'];
  if (lower.includes('on-site') || lower.includes('onsite') || lower.includes('on site')) {
    return ['On-site'];
  }
  return [];
};

export const RegistrationOnboarding: React.FC<RegistrationOnboardingProps> = ({
  firstName,
  onComplete,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const onboardingOrder: OnboardingStep[] = ['resume', 'profile', 'preferences', 'complete'];

  const [onboardingStatus, setOnboardingStatus] = useState<OnboardingStatus>({
    profile: 'pending',
    resume: 'pending',
    preferences: 'pending',
  });
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [resumeUploading, setResumeUploading] = useState(false);
  const [resumeFileName, setResumeFileName] = useState<string | null>(null);
  const [resumeMessage, setResumeMessage] = useState<string | null>(null);
  const [resumeError, setResumeError] = useState<string | null>(null);
  const [hasAutofilled, setHasAutofilled] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [profileDraft, setProfileDraft] = useState({
    title: '',
    location: '',
  });
  const [preferencesDraft, setPreferencesDraft] = useState({
    targetRole: '',
    workStyle: [] as string[],
  });

  const completedCount = Object.values(onboardingStatus).filter((state) => state !== 'pending').length;
  const totalSteps = 3;
  const allSetupStepsDone = completedCount === 3;
  const activeStep = onboardingOrder[activeStepIndex];
  const isLastStep = activeStepIndex === onboardingOrder.length - 1;
  const isFirstStep = activeStepIndex === 0;

  const updateStepStatus = (stepKey: OnboardingStep, status: OnboardingStepStatus) => {
    setOnboardingStatus((prev) => ({ ...prev, [stepKey]: status }));
  };

  const moveToNextStep = () => {
    setActiveStepIndex((prev) => Math.min(prev + 1, onboardingOrder.length - 1));
  };

  const moveToPreviousStep = () => {
    setActiveStepIndex((prev) => Math.max(prev - 1, 0));
  };

  const handleSkipCurrentStep = () => {
    if (activeStep === 'complete') {
      return;
    }

    if (onboardingStatus[activeStep] === 'pending') {
      updateStepStatus(activeStep, 'skipped');
    }
    if (!isLastStep) {
      moveToNextStep();
    }
  };

  const handleGoToStep = (index: number) => {
    if (index >= 0 && index < onboardingOrder.length) {
      setActiveStepIndex(index);
    }
  };

  const applyParsedDataToDrafts = (normalizedData: ResumeNormalizedData | null | undefined, extractedText?: string | null) => {
    if (!normalizedData) return;

    const inferredTitle = normalizedData.headline_title || normalizedData.current_job_title || '';
    const inferredLocation = normalizedData.experience_sections?.[0]?.location || '';
    const inferredTargetRole = normalizedData.current_job_title || normalizedData.headline_title || '';
    const inferredWorkStyle = inferWorkStyle(extractedText);

    setProfileDraft((prev) => ({
      title: prev.title || inferredTitle,
      location: prev.location || inferredLocation,
    }));

    setPreferencesDraft((prev) => ({
      targetRole: prev.targetRole || inferredTargetRole,
      workStyle: prev.workStyle.length > 0 ? prev.workStyle : inferredWorkStyle,
    }));

    if (inferredTitle || inferredLocation || inferredTargetRole || inferredWorkStyle) {
      setHasAutofilled(true);
    }
  };

  const processResumeFile = async (file: File) => {
    setResumeFileName(file.name);
    setResumeError(null);
    setResumeMessage(null);
    setResumeUploading(true);

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      if (!token) {
        throw new Error('You need to be signed in before uploading a resume.');
      }

      const response = await uploadResume(file, token);
      applyParsedDataToDrafts(response.parsed_json?.normalized_data, response.extracted_text);
      setResumeMessage(response.message || 'Resume uploaded and parsed.');
      updateStepStatus('resume', 'completed');

      if (activeStep === 'resume' && !isLastStep) {
        moveToNextStep();
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Resume upload failed. Please try again.';
      setResumeError(message);
      updateStepStatus('resume', 'pending');
    } finally {
      setResumeUploading(false);
    }
  };

  const handleResumeFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await processResumeFile(file);
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    await processResumeFile(file);
  };

  const handleStepAdvance = () => {
    if (activeStep === 'complete') {
      onComplete();
      return;
    }

    if (onboardingStatus[activeStep] === 'pending') {
      updateStepStatus(activeStep, 'completed');
    }

    if (!isLastStep) {
      moveToNextStep();
    }
  };

  const toggleWorkStyle = (workStyle: string) => {
    setPreferencesDraft((prev) => {
      const isSelected = prev.workStyle.includes(workStyle);
      return {
        ...prev,
        workStyle: isSelected
          ? prev.workStyle.filter((option) => option !== workStyle)
          : [...prev.workStyle, workStyle],
      };
    });
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4 sm:px-6 py-12">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Sparkles className="h-9 w-9 text-brand" />
            <span className="text-3xl font-semibold text-foreground">Artemis</span>
          </div>
          <h1 className="text-2xl font-semibold text-foreground">
            Welcome{firstName ? `, ${firstName}` : ''}!
          </h1>
          <p className="mt-2 text-muted-foreground">
            Let&apos;s get you set up so Artemis can start working for you.
          </p>
        </div>

        <div className="mb-6 p-4 rounded-xl bg-brand/5 border border-brand/20">
          <div className="flex items-start gap-3">
            <Zap className="h-5 w-5 text-brand flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-foreground">Artemis automates your job search</p>
              <p className="text-sm text-muted-foreground mt-0.5">
                Track applications, get AI-tailored resume suggestions, and stay on top of follow-ups
                in one place. Complete the steps below to unlock the full experience.
              </p>
            </div>
          </div>
        </div>

        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-foreground">Setup progress</span>
            <span className="text-sm text-muted-foreground">
              {activeStep === 'complete'
                ? `Step ${totalSteps} of ${totalSteps} done`
                : `${completedCount} of ${totalSteps} steps done`}
            </span>
          </div>
          <div className="h-2 rounded-full bg-secondary overflow-hidden">
            <div
              className="h-full rounded-full bg-brand transition-all duration-500"
              style={{
                width: `${(completedCount / totalSteps) * 100}%`,
              }}
            />
          </div>
        </div>

        <div className="mb-4 flex items-center justify-center gap-2">
          {onboardingOrder.map((stepName, index) => {
            const status =
              stepName === 'complete' ? (allSetupStepsDone ? 'completed' : 'pending') : onboardingStatus[stepName];
            const isActive = index === activeStepIndex;
            return (
              <button
                key={stepName}
                type="button"
                onClick={() => handleGoToStep(index)}
                className={`h-2.5 rounded-full transition-all ${
                  isActive ? 'w-8 bg-brand' : 'w-2.5 bg-secondary'
                } ${status !== 'pending' && !isActive ? 'bg-brand/60' : ''}`}
                aria-label={`Go to ${stepName} step`}
              />
            );
          })}
        </div>

        <Card>
          <div className="space-y-4">
            {activeStep === 'resume' && (
              <div className="p-4 rounded-xl border-2 border-brand/50 bg-brand/5">
                <div className="flex items-start gap-3 mb-3">
                  <Upload className="h-5 w-5 text-brand mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-foreground">Step 1: Upload your resume</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      Start here. Artemis will parse your resume to accelerate profile setup and job matching.
                    </p>
                  </div>
                </div>
                {resumeUploading && (
                  <div className="mb-3 px-3 py-2 rounded-lg border border-brand/25 bg-brand/10 flex items-center gap-2">
                    <Loader2 className="h-4 w-4 text-brand animate-spin" />
                    <p className="text-xs text-foreground">Uploading and parsing your resume...</p>
                  </div>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.doc,.docx,.txt"
                  className="hidden"
                  onChange={handleResumeFileChange}
                />
                <div
                  className={`mt-1 border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
                    isDragOver
                      ? 'border-brand bg-brand/10'
                      : onboardingStatus.resume === 'completed'
                      ? 'border-brand/60 bg-brand/5'
                      : 'border-border hover:border-brand hover:bg-brand/5'
                  }`}
                  onClick={() => !resumeUploading && fileInputRef.current?.click()}
                  onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                  onDragEnter={(e) => { e.preventDefault(); setIsDragOver(true); }}
                  onDragLeave={() => setIsDragOver(false)}
                  onDrop={handleDrop}
                >
                  {onboardingStatus.resume === 'completed' ? (
                    <div className="flex flex-col items-center gap-2">
                      <CheckCircle className="h-10 w-10 text-brand" />
                      <p className="text-sm font-medium text-foreground">{resumeFileName}</p>
                      <p className="text-xs text-muted-foreground">Resume uploaded successfully</p>
                    </div>
                  ) : resumeUploading ? (
                    <div className="flex flex-col items-center gap-2">
                      <Upload className="h-10 w-10 text-brand animate-pulse" />
                      <p className="text-sm text-muted-foreground">Uploading {resumeFileName}…</p>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-2">
                      <div className="h-14 w-14 rounded-full bg-brand/10 flex items-center justify-center mb-1">
                        <Upload className="h-7 w-7 text-brand" />
                      </div>
                      <p className="text-sm font-medium text-foreground">Drag and drop your resume here</p>
                      <p className="text-xs text-muted-foreground">or click to browse</p>
                      <p className="text-xs text-muted-foreground mt-1">PDF, DOC, DOCX, TXT · Max 5MB</p>
                    </div>
                  )}
                </div>
                {resumeMessage && (
                  <p className="text-xs text-brand mt-3">{resumeMessage}</p>
                )}
                {resumeError && (
                  <p className="text-xs text-destructive mt-3">{resumeError}</p>
                )}
              </div>
            )}

            {activeStep === 'profile' && (
              <div className="p-4 rounded-xl border border-border bg-secondary/20">
                <div className="flex items-start gap-3 mb-4">
                  <User className="h-5 w-5 text-brand mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-foreground">Step 2: Profile basics</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      Add a few essentials now. You can always refine your profile later.
                    </p>
                  </div>
                </div>
                {hasAutofilled && (
                  <div className="mb-4 px-3 py-2 rounded-lg bg-brand/10 border border-brand/25">
                    <p className="text-xs text-foreground">
                      We auto-filled this step from your resume. Review and edit anything that looks off.
                    </p>
                  </div>
                )}
                <div className="space-y-3">
                  <Input
                    type="text"
                    label="Professional Title"
                    placeholder="e.g., Product Manager"
                    value={profileDraft.title}
                    onChange={(e) => setProfileDraft((prev) => ({ ...prev, title: e.target.value }))}
                    fullWidth
                  />
                  <Input
                    type="text"
                    label="Location"
                    placeholder="e.g., Chicago, IL"
                    value={profileDraft.location}
                    onChange={(e) => setProfileDraft((prev) => ({ ...prev, location: e.target.value }))}
                    fullWidth
                  />
                </div>
              </div>
            )}

            {activeStep === 'preferences' && (
              <div className="p-4 rounded-xl border border-border bg-secondary/20">
                <div className="flex items-start gap-3 mb-4">
                  <Briefcase className="h-5 w-5 text-brand mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-foreground">Step 3: Job preferences</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      Tell Artemis what kind of opportunities you want to prioritize.
                    </p>
                  </div>
                </div>
                {hasAutofilled && (
                  <div className="mb-4 px-3 py-2 rounded-lg bg-brand/10 border border-brand/25">
                    <p className="text-xs text-foreground">
                      This step was pre-filled from parsed resume data. You can adjust preferences now.
                    </p>
                  </div>
                )}
                <div className="space-y-3">
                  <Input
                    type="text"
                    label="Target Role"
                    placeholder="e.g., Senior Product Manager"
                    value={preferencesDraft.targetRole}
                    onChange={(e) =>
                      setPreferencesDraft((prev) => ({ ...prev, targetRole: e.target.value }))
                    }
                    fullWidth
                  />
                  <div>
                    <p className="text-sm font-medium text-foreground mb-2">Work Style</p>
                    <div className="space-y-2">
                      {['Remote', 'Hybrid', 'On-site'].map((option) => (
                        <label key={option} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={preferencesDraft.workStyle.includes(option)}
                            onChange={() => toggleWorkStyle(option)}
                            className="h-4 w-4 rounded border-border text-brand cursor-pointer"
                          />
                          <span className="text-sm text-foreground">{option}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeStep === 'complete' && (
              <div className="p-6 rounded-xl border border-brand/30 bg-brand/10">
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-6 w-6 text-brand mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-foreground">All set!</h3>
                    <p className="text-sm text-muted-foreground mt-2">
                      You&apos;re done onboarding. Your resume is parsed, your setup is complete,
                      and Artemis is ready to help you move faster.
                    </p>
                    <p className="text-sm text-muted-foreground mt-2">
                      Continue to your dashboard to start tracking jobs and applications.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {!allSetupStepsDone && (
            <div className="mt-4 px-4 py-3 rounded-lg bg-secondary/60 border border-border">
              <p className="text-xs text-muted-foreground">
                <span className="font-medium text-foreground">Tip:</span> Job feed matching and
                application automation work best once your profile and resume are both complete.
              </p>
            </div>
          )}

          {allSetupStepsDone && activeStep !== 'complete' && (
            <div className="mt-4 px-4 py-3 rounded-lg bg-brand/10 border border-brand/30 flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-brand flex-shrink-0" />
              <p className="text-sm text-foreground font-medium">
                Setup complete. Review the final step, then continue to your dashboard.
              </p>
            </div>
          )}

          <div className="flex items-center justify-between pt-6 border-t border-border mt-2">
            <div className="flex items-center gap-2">
              {!isFirstStep && (
                <Button variant="ghost" size="sm" onClick={moveToPreviousStep}>
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </Button>
              )}
              {activeStep !== 'complete' && (
                <Button variant="ghost" size="sm" onClick={handleSkipCurrentStep}>
                  Skip Step
                </Button>
              )}
            </div>
            <Button variant="primary" onClick={handleStepAdvance} disabled={resumeUploading}>
              {activeStep === 'complete' ? 'Go to Dashboard' : isLastStep ? 'Finish' : 'Next Step'}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};
