'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AlertTriangle, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { AppShell } from '../components/AppShell';
import { Card, CardContent, CardHeader, CardTitle, Input } from '../components/ui';
import { SimpleExperienceEditor, type SimpleExperience } from '../components/profile/SimpleExperienceEditor';
import {
  getStoredAccessToken,
} from '../../services/auth/auth.service';
import {
  getProfile,
  updateProfile,
  type CandidateExperienceSection,
  type CandidateProfile,
  type CandidateProfileUpdateRequest,
} from '../../services/profile/profile.service';

type SaveStatus = 'idle' | 'saving' | 'saved' | 'error';

const UNSAVED_PROFILE_TOAST_ID = 'unsaved-profile-toast';

function toFormData(profile: CandidateProfile) {
  return {
    phone: profile.phone ?? '',
    city: profile.city ?? '',
    state: profile.state ?? '',
    country: profile.country ?? '',
    zip_code: profile.zip_code ?? '',
    current_company: profile.current_company ?? '',
    linkedin_url: profile.linkedin_url ?? '',
    github_url: profile.github_url ?? '',
    portfolio_url: profile.portfolio_url ?? '',
  };
}

type FormData = ReturnType<typeof toFormData>;

const MONTH_PREFIX_TO_NAME: Record<string, string> = {
  jan: 'January',
  feb: 'February',
  mar: 'March',
  apr: 'April',
  may: 'May',
  jun: 'June',
  jul: 'July',
  aug: 'August',
  sep: 'September',
  sept: 'September',
  oct: 'October',
  nov: 'November',
  dec: 'December',
};

function parseMonthYear(value?: string | null): { month: string; year: string } {
  const raw = value?.trim();
  if (!raw) return { month: '', year: '' };

  const match = raw.match(/^([A-Za-z]+)\s+(\d{4})$/);
  if (match) {
    const [, monthRaw, year] = match;
    const normalizedMonth = MONTH_PREFIX_TO_NAME[monthRaw.toLowerCase().slice(0, 4)] || monthRaw;
    return { month: normalizedMonth, year };
  }

  const yearOnly = raw.match(/^(\d{4})$/);
  if (yearOnly) {
    return { month: '', year: yearOnly[1] };
  }

  return { month: '', year: '' };
}

function mapApiExperienceToSimple(exp: CandidateExperienceSection, index: number): SimpleExperience {
  const role = exp.role?.trim() || exp.position?.trim() || '';
  const company = exp.company?.trim() ?? '';
  const parsedStart = parseMonthYear(exp.start_date);
  const parsedEnd = parseMonthYear(exp.end_date);
  const startMonth = exp.start_month?.trim() || parsedStart.month;
  const startYear = exp.start_year?.trim() || parsedStart.year;
  const endMonth = exp.end_month?.trim() || parsedEnd.month;
  const endYear = exp.end_year?.trim() || parsedEnd.year;
  const isCurrentFromEndDate = (exp.end_date?.trim().toLowerCase() ?? '') === 'current';
  const fallbackId = `exp-${company || 'company'}-${role || 'role'}-${startYear || 'start'}-${index}`;

  return {
    id: exp.id?.trim() || fallbackId,
    role,
    company,
    startMonth,
    startYear,
    endMonth,
    endYear,
    currentlyWorking: Boolean(exp.currently_working) || isCurrentFromEndDate,
    details: (exp.details ?? []).map((detail) => detail.trim()).filter(Boolean),
  };
}

function mapSimpleExperienceToApi(exp: SimpleExperience): CandidateExperienceSection {
  return {
    id: exp.id,
    role: exp.role,
    company: exp.company,
    start_month: exp.startMonth,
    start_year: exp.startYear,
    end_month: exp.endMonth,
    end_year: exp.endYear,
    currently_working: exp.currentlyWorking,
    details: exp.details,
  };
}

export const ProfileSettings: React.FC = () => {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData | null>(null);
  const [originalData, setOriginalData] = useState<FormData | null>(null);
  const [experiences, setExperiences] = useState<SimpleExperience[]>([]);
  const [originalExperiences, setOriginalExperiences] = useState<SimpleExperience[]>([]);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle');
  const [saveError, setSaveError] = useState<string | null>(null);

  const isDirty =
    formData && originalData
      ? JSON.stringify(formData) !== JSON.stringify(originalData)
        || JSON.stringify(experiences) !== JSON.stringify(originalExperiences)
      : false;

  useEffect(() => {
    const token = getStoredAccessToken();
    if (!token) { router.push('/signin'); return; }

    const load = async () => {
      try {
        const profile = await getProfile(token);
        const fd = toFormData(profile);
        setFormData(fd);
        setOriginalData(fd);
        const mappedExperiences = (profile.experience_sections ?? []).map((exp, index) =>
          mapApiExperienceToSimple(exp, index),
        );
        setExperiences(mappedExperiences);
        setOriginalExperiences(mappedExperiences);
      } catch {
        setLoadError('Unable to load your profile. Please try refreshing the page.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [router]);

  const setField = <K extends keyof FormData>(key: K, value: FormData[K]) => {
    setFormData((prev) => (prev ? { ...prev, [key]: value } : prev));
  };

  const handleSave = useCallback(async () => {
    if (!formData) return;
    const token = getStoredAccessToken();
    if (!token) { router.push('/signin'); return; }

    toast.dismiss(UNSAVED_PROFILE_TOAST_ID);
    setSaveStatus('saving');
    setSaveError(null);

    const payload: CandidateProfileUpdateRequest = {
      phone: formData.phone || null,
      city: formData.city || null,
      state: formData.state || null,
      country: formData.country || null,
      zip_code: formData.zip_code || null,
      current_company: formData.current_company || null,
      linkedin_url: formData.linkedin_url || null,
      github_url: formData.github_url || null,
      portfolio_url: formData.portfolio_url || null,
      experience_sections: experiences.length > 0 ? experiences.map(mapSimpleExperienceToApi) : null,
    };

    try {
      await updateProfile(token, payload);
      setOriginalData(formData);
      setOriginalExperiences(experiences);
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (err) {
      setSaveStatus('error');
      setSaveError(err instanceof Error ? err.message : 'Failed to save profile.');
    }
  }, [experiences, formData, router]);

  useEffect(() => {
    if (!isDirty || saveStatus === 'saving') {
      toast.dismiss(UNSAVED_PROFILE_TOAST_ID);
      return;
    }

    toast('Unsaved Changes', {
      id: UNSAVED_PROFILE_TOAST_ID,
      duration: Infinity,
      position: 'bottom-center',
      description: 'Save your profile to apply updates.',
      actionButtonStyle: {
        background: 'var(--brand)',
        color: 'var(--brand-foreground)',
        border: '1px solid var(--brand)',
      },
      action: {
        label: 'Save',
        onClick: handleSave,
      },
    });
  }, [isDirty, saveStatus, handleSave]);

  if (loading) {
    return (
      <AppShell>
        <div className="max-w-4xl mx-auto animate-pulse space-y-6">
          <div className="h-16 bg-muted rounded-lg" />
          <div className="h-52 bg-muted rounded-lg" />
          <div className="h-48 bg-muted rounded-lg" />
          <div className="h-52 bg-muted rounded-lg" />
        </div>
      </AppShell>
    );
  }

  if (loadError || !formData) {
    return (
      <AppShell>
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3 p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-destructive">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <span>{loadError ?? 'Unable to load profile.'}</span>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto">
        {/* Header Actions */}
        <div className="mb-8 flex items-center justify-end gap-3">
            {isDirty && saveStatus === 'idle' && (
              <span className="text-sm text-muted-foreground">Unsaved changes</span>
            )}
            {saveStatus === 'saved' && (
              <div className="flex items-center gap-1.5 text-success text-sm">
                <CheckCircle className="h-4 w-4" />
                <span>Saved</span>
              </div>
            )}
            {saveStatus === 'error' && (
              <span className="text-sm text-destructive">{saveError}</span>
            )}
          </div>

        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-foreground">Candidate Information</h2>
            <p className="text-sm text-muted-foreground mt-1">Core profile details used across applications.</p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Personal Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input label="Phone" type="tel" value={formData.phone} onChange={(e) => setField('phone', e.target.value)} fullWidth placeholder="+1 (555) 000-0000" />
                <Input label="Current Company" value={formData.current_company} onChange={(e) => setField('current_company', e.target.value)} fullWidth />
                <Input label="City" value={formData.city} onChange={(e) => setField('city', e.target.value)} fullWidth />
                <Input label="State / Province" value={formData.state} onChange={(e) => setField('state', e.target.value)} fullWidth />
                <Input label="Country" value={formData.country} onChange={(e) => setField('country', e.target.value)} fullWidth placeholder="United States" />
                <Input label="ZIP / Postal Code" value={formData.zip_code} onChange={(e) => setField('zip_code', e.target.value)} fullWidth />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Professional Links</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input label="LinkedIn" value={formData.linkedin_url} onChange={(e) => setField('linkedin_url', e.target.value)} fullWidth placeholder="https://linkedin.com/in/yourprofile" />
                <Input label="GitHub" value={formData.github_url} onChange={(e) => setField('github_url', e.target.value)} fullWidth placeholder="https://github.com/yourusername" />
                <div className="md:col-span-2">
                  <Input label="Portfolio" value={formData.portfolio_url} onChange={(e) => setField('portfolio_url', e.target.value)} fullWidth placeholder="https://yourwebsite.com" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <SimpleExperienceEditor experiences={experiences} onChange={setExperiences} />
            </CardContent>
          </Card>

        </div>
      </div>
    </AppShell>
  );
};
