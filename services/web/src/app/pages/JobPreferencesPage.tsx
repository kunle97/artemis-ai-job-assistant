'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { AppShell } from '../components/AppShell';
import { Badge, Card, CardContent, CardHeader, CardTitle, Input } from '../components/ui';
import { X, Sparkles } from 'lucide-react';
import { getStoredAccessToken } from '../../services/auth/auth.service';
import {
  getProfile,
  updateProfile,
  type CandidateProfile,
  type CandidateProfileUpdateRequest,
} from '../../services/profile/profile.service';
import {
  getJobPreferences,
  updateJobPreferences,
  type JobPreferences,
} from '../../services/jobs/job-preferences.service';

const UNSAVED_JOB_PREF_TOAST_ID = 'unsaved-job-preferences-toast';

const WORK_ARRANGEMENT_OPTIONS = [
  { value: 'remote', label: 'Remote' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'onsite', label: 'On-site' },
];

type FormData = {
  salary_target: string;
  min_salary: string;
  work_arrangement: string[];
  preferred_relocation_cities: string[];
  skills: string[];
  target_job_titles: string[];
  target_keywords: string[];
  negative_keywords: string[];
  enabled_sources: string[];
  remote_only: boolean;
};

type ChipField = 'target_job_titles' | 'target_keywords' | 'skills' | 'negative_keywords';

function toFormData(profile: CandidateProfile, jobPreferences: JobPreferences): FormData {
  return {
    salary_target: profile.salary_target ?? '',
    min_salary: profile.min_salary ?? '',
    work_arrangement: profile.work_arrangement ?? [],
    preferred_relocation_cities: profile.preferred_relocation_cities ?? [],
    skills: profile.skills ?? [],
    target_job_titles: jobPreferences.target_titles ?? [],
    target_keywords: jobPreferences.positive_keywords ?? [],
    negative_keywords: jobPreferences.negative_keywords ?? [],
    enabled_sources: jobPreferences.enabled_sources ?? [],
    remote_only: jobPreferences.remote_only ?? false,
  };
}

export const JobPreferencesPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState<FormData | null>(null);
  const [originalData, setOriginalData] = useState<FormData | null>(null);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving'>('idle');
  const [showFeedImpactPrompt, setShowFeedImpactPrompt] = useState(true);
  const [relocationCityQuery, setRelocationCityQuery] = useState('');
  const [targetTitleQuery, setTargetTitleQuery] = useState('');
  const [targetKeywordQuery, setTargetKeywordQuery] = useState('');
  const [negativeKeywordQuery, setNegativeKeywordQuery] = useState('');
  const [skillQuery, setSkillQuery] = useState('');

  const isDirty =
    formData && originalData
      ? JSON.stringify(formData) !== JSON.stringify(originalData)
      : false;

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const dismissed = window.localStorage.getItem('dismissed_job_feed_impact_prompt');
    if (dismissed === 'true') {
      setShowFeedImpactPrompt(false);
    }
  }, []);

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) return;

    const load = async () => {
      try {
        const [profile, jobPreferences] = await Promise.all([
          getProfile(token),
          getJobPreferences(token),
        ]);
        const fd = toFormData(profile, jobPreferences);
        setFormData(fd);
        setOriginalData(fd);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const setField = <K extends keyof FormData>(key: K, value: FormData[K]) => {
    setFormData((prev) => (prev ? { ...prev, [key]: value } : prev));
  };

  const addChipValue = useCallback((field: ChipField, value: string, onAdded?: () => void) => {
    const normalized = value.trim();
    if (!normalized) return;

    setFormData((prev) => {
      if (!prev) return prev;
      const exists = prev[field].some((entry) => entry.toLowerCase() === normalized.toLowerCase());
      if (exists) return prev;
      return {
        ...prev,
        [field]: [...prev[field], normalized],
      };
    });

    if (onAdded) onAdded();
  }, []);

  const removeChipValue = (field: ChipField, value: string) => {
    setFormData((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        [field]: prev[field].filter((entry) => entry !== value),
      };
    });
  };

  const toggleWorkArrangement = (value: string) => {
    setFormData((prev) => {
      if (!prev) return prev;
      const updated = prev.work_arrangement.includes(value)
        ? prev.work_arrangement.filter((v) => v !== value)
        : [...prev.work_arrangement, value];
      return { ...prev, work_arrangement: updated };
    });
  };

  const addRelocationCity = useCallback((value: string) => {
    const city = value.trim();
    if (!city) return;

    setFormData((prev) => {
      if (!prev) return prev;
      const exists = prev.preferred_relocation_cities.some(
        (existingCity) => existingCity.toLowerCase() === city.toLowerCase(),
      );
      if (exists) return prev;
      return {
        ...prev,
        preferred_relocation_cities: [...prev.preferred_relocation_cities, city],
      };
    });

    setRelocationCityQuery('');
  }, []);

  const removeRelocationCity = (cityToRemove: string) => {
    setFormData((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        preferred_relocation_cities: prev.preferred_relocation_cities.filter(
          (city) => city !== cityToRemove,
        ),
      };
    });
  };

  const handleSave = useCallback(async () => {
    if (!formData) return;
    const token = getStoredAccessToken();
    if (!token) return;

    toast.dismiss(UNSAVED_JOB_PREF_TOAST_ID);
    setSaveStatus('saving');

    const payload: CandidateProfileUpdateRequest = {
      salary_target: formData.salary_target || null,
      min_salary: formData.min_salary || null,
      skills: formData.skills.length > 0 ? formData.skills : null,
      work_arrangement: formData.work_arrangement.length > 0 ? formData.work_arrangement : null,
      preferred_relocation_cities: formData.preferred_relocation_cities.length > 0
        ? formData.preferred_relocation_cities
        : null,
    };

    const jobPreferencesPayload: JobPreferences = {
      target_titles: formData.target_job_titles,
      positive_keywords: formData.target_keywords,
      negative_keywords: formData.negative_keywords,
      locations: formData.preferred_relocation_cities,
      remote_only: formData.remote_only,
      salary_min: formData.min_salary ? Number.parseInt(formData.min_salary, 10) || null : null,
      enabled_sources: formData.enabled_sources,
    };

    await Promise.all([
      updateProfile(token, payload),
      updateJobPreferences(token, jobPreferencesPayload),
    ]);
    setOriginalData(formData);
    setSaveStatus('idle');
    toast.success('Preferences saved', { description: 'Your job targeting settings have been updated.' });
  }, [formData]);

  const handleSaveWithError = useCallback(async () => {
    try {
      await handleSave();
    } catch {
      setSaveStatus('idle');
      toast.error('Failed to save preferences', { description: 'Please try again in a moment.' });
    }
  }, [handleSave]);

  useEffect(() => {
    if (!isDirty || saveStatus === 'saving') {
      toast.dismiss(UNSAVED_JOB_PREF_TOAST_ID);
      return;
    }

    toast('Unsaved Changes', {
      id: UNSAVED_JOB_PREF_TOAST_ID,
      duration: Infinity,
      position: 'bottom-center',
      description: 'Save your job preferences to apply updates.',
      actionButtonStyle: {
        background: 'var(--brand)',
        color: 'var(--brand-foreground)',
        border: '1px solid var(--brand)',
      },
      action: {
        label: 'Save',
        onClick: handleSaveWithError,
      },
    });
  }, [handleSaveWithError, isDirty, saveStatus]);

  if (loading || !formData) {
    return (
      <AppShell>
        <div className="max-w-4xl mx-auto animate-pulse space-y-6">
          <div className="h-16 bg-muted rounded-lg" />
          <div className="h-48 bg-muted rounded-lg" />
          <div className="h-52 bg-muted rounded-lg" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto">
        <div className="space-y-6">
          <div className="pt-2">
            <h2 className="text-lg font-semibold text-foreground">Preference Options</h2>
            <p className="text-sm text-muted-foreground mt-1">Job targeting and autofill behaviors for your feed.</p>
          </div>

          {showFeedImpactPrompt && (
            <Card variant="outlined" className="bg-brand/5 border-brand/20">
              <CardContent className="pt-6">
                <div className="flex gap-3">
                  <Sparkles className="h-5 w-5 text-brand flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground mb-1">How this affects your feed</p>
                    <p className="text-sm text-muted-foreground">
                      Artemis uses these preferences to score and filter job opportunities. More specific preferences lead to better matches but may reduce the number of results. You can always adjust these settings based on what you're seeing.
                    </p>
                  </div>
                  <button
                    type="button"
                    aria-label="Dismiss feed impact prompt"
                    onClick={() => {
                      setShowFeedImpactPrompt(false);
                      if (typeof window !== 'undefined') {
                        window.localStorage.setItem('dismissed_job_feed_impact_prompt', 'true');
                      }
                    }}
                    className="rounded-md p-1 text-muted-foreground hover:bg-secondary hover:text-foreground"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Role Targeting</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Input
                  label="Target Job Titles"
                  value={targetTitleQuery}
                  onChange={(e) => setTargetTitleQuery(e.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ',') {
                      event.preventDefault();
                      addChipValue('target_job_titles', targetTitleQuery, () => setTargetTitleQuery(''));
                    }
                  }}
                  fullWidth
                  placeholder="e.g. Software Engineer, Frontend Developer — press Enter to add"
                />
                <p className="mt-1 text-xs text-muted-foreground">Artemis will prioritize jobs matching these titles. Add variations like &quot;SWE&quot; and &quot;Software Engineer&quot;.</p>
                {formData.target_job_titles.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {formData.target_job_titles.map((title) => (
                      <Badge key={title} variant="secondary" className="inline-flex items-center gap-1.5 pr-1">
                        <span>{title}</span>
                        <button
                          type="button"
                          onClick={() => removeChipValue('target_job_titles', title)}
                          className="rounded-sm p-0.5 hover:bg-secondary-foreground/10"
                          aria-label={`Remove ${title}`}
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <Input
                  label="Keywords to include"
                  value={targetKeywordQuery}
                  onChange={(e) => setTargetKeywordQuery(e.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ',') {
                      event.preventDefault();
                      addChipValue('target_keywords', targetKeywordQuery, () => setTargetKeywordQuery(''));
                    }
                  }}
                  fullWidth
                  placeholder="e.g. React, TypeScript — press Enter to add"
                />
                <p className="mt-1 text-xs text-muted-foreground">Jobs containing these terms will be ranked higher in your feed.</p>
                {formData.target_keywords.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {formData.target_keywords.map((keyword) => (
                      <Badge key={keyword} variant="secondary" className="inline-flex items-center gap-1.5 pr-1">
                        <span>{keyword}</span>
                        <button
                          type="button"
                          onClick={() => removeChipValue('target_keywords', keyword)}
                          className="rounded-sm p-0.5 hover:bg-secondary-foreground/10"
                          aria-label={`Remove ${keyword}`}
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <Input
                  label="Keywords to exclude"
                  value={negativeKeywordQuery}
                  onChange={(e) => setNegativeKeywordQuery(e.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ',') {
                      event.preventDefault();
                      addChipValue('negative_keywords', negativeKeywordQuery, () => setNegativeKeywordQuery(''));
                    }
                  }}
                  fullWidth
                  placeholder="e.g. manager, director — press Enter to add"
                />
                <p className="mt-1 text-xs text-muted-foreground">Jobs containing these terms will be ranked lower or hidden from your feed.</p>
                {formData.negative_keywords.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {formData.negative_keywords.map((keyword) => (
                      <Badge key={keyword} variant="destructive" className="inline-flex items-center gap-1.5 pr-1">
                        <span>{keyword}</span>
                        <button
                          type="button"
                          onClick={() => removeChipValue('negative_keywords', keyword)}
                          className="rounded-sm p-0.5 hover:bg-destructive-foreground/10"
                          aria-label={`Remove ${keyword}`}
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <Input
                label="Skills"
                value={skillQuery}
                onChange={(e) => setSkillQuery(e.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ',') {
                    event.preventDefault();
                    addChipValue('skills', skillQuery, () => setSkillQuery(''));
                  }
                }}
                fullWidth
                placeholder="Add a skill, then press Enter"
              />
              {formData.skills.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {formData.skills.map((skill) => (
                    <Badge key={skill} variant="secondary" className="inline-flex items-center gap-1.5 pr-1">
                      <span>{skill}</span>
                      <button
                        type="button"
                        onClick={() => removeChipValue('skills', skill)}
                        className="rounded-sm p-0.5 hover:bg-secondary-foreground/10"
                        aria-label={`Remove ${skill}`}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Work Preferences</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input label="Target Salary" value={formData.salary_target} onChange={(e) => setField('salary_target', e.target.value)} fullWidth placeholder="e.g. $120,000" />
                <Input label="Minimum Salary" value={formData.min_salary} onChange={(e) => setField('min_salary', e.target.value)} fullWidth placeholder="e.g. $90,000" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground mb-2">Work Arrangement</p>
                <div className="flex flex-wrap gap-4">
                  {WORK_ARRANGEMENT_OPTIONS.map((opt) => (
                    <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.work_arrangement.includes(opt.value)}
                        onChange={() => toggleWorkArrangement(opt.value)}
                        className="h-4 w-4 rounded border-border text-brand"
                      />
                      <span className="text-sm text-foreground">{opt.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex items-start gap-3 rounded-lg border border-border p-3">
                <input
                  id="remote-only"
                  type="checkbox"
                  checked={formData.remote_only}
                  onChange={(e) => setField('remote_only', e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded border-border text-brand"
                />
                <div>
                  <label htmlFor="remote-only" className="text-sm font-medium text-foreground cursor-pointer">
                    Remote only (hard filter)
                  </label>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    When enabled, non-remote jobs are excluded entirely from your feed — not just ranked lower.
                  </p>
                </div>
              </div>
              <div>
                <Input
                  label="Preferred Relocation Cities"
                  value={relocationCityQuery}
                  onChange={(e) => setRelocationCityQuery(e.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ',') {
                      event.preventDefault();
                      addRelocationCity(relocationCityQuery);
                    }
                  }}
                  fullWidth
                  placeholder="Search or add a city, then press Enter"
                />
                {formData.preferred_relocation_cities.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {formData.preferred_relocation_cities.map((city) => (
                      <Badge key={city} variant="secondary" className="inline-flex items-center gap-1.5 pr-1">
                        <span>{city}</span>
                        <button
                          type="button"
                          onClick={() => removeRelocationCity(city)}
                          className="rounded-sm p-0.5 hover:bg-secondary-foreground/10"
                          aria-label={`Remove ${city}`}
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

        </div>
      </div>
    </AppShell>
  );
};
