'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AlertTriangle, CheckCircle, Save, X } from 'lucide-react';
import { toast } from 'sonner';
import { AppShell } from '../components/AppShell';
import { Badge, Button, Card, CardHeader, CardTitle, CardContent, Input } from '../components/ui';
import { SimpleExperienceEditor, type SimpleExperience } from '../components/profile/SimpleExperienceEditor';
import {
  DemographicAutofillPreferences,
  type DemographicAutofillSettings,
} from '../components/profile/DemographicAutofillPreferences';
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

const WORK_ARRANGEMENT_OPTIONS = [
  { value: 'remote', label: 'Remote' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'onsite', label: 'On-site' },
];

function toFormData(profile: CandidateProfile) {
  return {
    phone: profile.phone ?? '',
    city: profile.city ?? '',
    state: profile.state ?? '',
    country: profile.country ?? '',
    zip_code: profile.zip_code ?? '',
    salary_target: profile.salary_target ?? '',
    min_salary: profile.min_salary ?? '',
    current_company: profile.current_company ?? '',
    linkedin_url: profile.linkedin_url ?? '',
    github_url: profile.github_url ?? '',
    portfolio_url: profile.portfolio_url ?? '',
    skills: profile.skills ?? [],
    target_job_titles: [],
    target_keywords: [],
    work_arrangement: profile.work_arrangement ?? [],
    preferred_relocation_cities: profile.preferred_relocation_cities ?? [],

    gender: profile.gender ?? '',
    race: profile.race ?? '',
    veteran_status: profile.veteran_status ?? '',
    disability_status: profile.disability_status ?? '',
    pronouns: profile.pronouns ?? '',

    autofill_gender: profile.autofill_gender,
    autofill_race: profile.autofill_race,
    autofill_veteran_status: profile.autofill_veteran_status,
    autofill_disability_status: profile.autofill_disability_status,
    autofill_pronouns: profile.autofill_pronouns,
  };
}

type FormData = ReturnType<typeof toFormData>;

type ChipField = 'target_job_titles' | 'target_keywords' | 'skills';

function mapApiExperienceToSimple(exp: CandidateExperienceSection, index: number): SimpleExperience {
  const role = exp.role?.trim() ?? '';
  const company = exp.company?.trim() ?? '';
  const startMonth = exp.start_month?.trim() ?? '';
  const startYear = exp.start_year?.trim() ?? '';
  const endMonth = exp.end_month?.trim() ?? '';
  const endYear = exp.end_year?.trim() ?? '';
  const fallbackId = `exp-${company || 'company'}-${role || 'role'}-${startYear || 'start'}-${index}`;

  return {
    id: exp.id?.trim() || fallbackId,
    role,
    company,
    startMonth,
    startYear,
    endMonth,
    endYear,
    currentlyWorking: Boolean(exp.currently_working),
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
  const [relocationCityQuery, setRelocationCityQuery] = useState('');
  const [targetTitleQuery, setTargetTitleQuery] = useState('');
  const [targetKeywordQuery, setTargetKeywordQuery] = useState('');
  const [skillQuery, setSkillQuery] = useState('');

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

  const demographicSettings: DemographicAutofillSettings = {
    race: { value: formData?.race ?? '', autofill: formData?.autofill_race ?? false },
    gender: { value: formData?.gender ?? '', autofill: formData?.autofill_gender ?? false },
    veteranStatus: {
      value: formData?.veteran_status ?? '',
      autofill: formData?.autofill_veteran_status ?? false,
    },
    disabilityStatus: {
      value: formData?.disability_status ?? '',
      autofill: formData?.autofill_disability_status ?? false,
    },
    pronouns: { value: formData?.pronouns ?? '', autofill: formData?.autofill_pronouns ?? false },
  };

  const handleDemographicsChange = (settings: DemographicAutofillSettings) => {
    if (!formData) return;
    setFormData({
      ...formData,
      race: settings.race.value,
      gender: settings.gender.value,
      veteran_status: settings.veteranStatus.value,
      disability_status: settings.disabilityStatus.value,
      pronouns: settings.pronouns.value,
      autofill_race: settings.race.autofill,
      autofill_gender: settings.gender.autofill,
      autofill_veteran_status: settings.veteranStatus.autofill,
      autofill_disability_status: settings.disabilityStatus.autofill,
      autofill_pronouns: settings.pronouns.autofill,
    });
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
