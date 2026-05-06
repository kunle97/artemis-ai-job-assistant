import React, { useState, useEffect } from 'react';
import { AppShell } from '../components/AppShell';
import { Button, Card, CardHeader, CardTitle, CardContent } from '../components/ui';
import {
  SkillEditor,
  Skill,
  ExperienceEditor,
  Experience,
  DemographicPreferences,
  DemographicData,
  AutofillControls,
  AutofillSettings,
} from '../components/profile';
import { Save, X, RotateCcw, CheckCircle, AlertCircle } from 'lucide-react';

export const ProfileManagementPage: React.FC = () => {
  // State for all profile data
  const [skills, setSkills] = useState<Skill[]>([
    { id: '1', name: 'React', proficiency: 'Advanced', category: 'Technical' },
    { id: '2', name: 'TypeScript', proficiency: 'Advanced', category: 'Technical' },
    { id: '3', name: 'Leadership', proficiency: 'Intermediate', category: 'Soft Skills' },
  ]);

  const [experiences, setExperiences] = useState<Experience[]>([
    {
      id: '1',
      role: 'Senior Software Engineer',
      company: 'TechCorp',
      startDate: '2021-06',
      endDate: null,
      currentlyWorking: true,
      location: 'San Francisco, CA',
      summary: '• Led development of core platform features\n• Mentored junior engineers\n• Improved system performance by 40%',
    },
    {
      id: '2',
      role: 'Software Engineer',
      company: 'StartupXYZ',
      startDate: '2019-01',
      endDate: '2021-05',
      currentlyWorking: false,
      location: 'Remote',
      summary: '• Built scalable microservices architecture\n• Implemented CI/CD pipelines',
    },
  ]);

  const [demographicData, setDemographicData] = useState<DemographicData>({});

  const [autofillSettings, setAutofillSettings] = useState<AutofillSettings>({
    enabled: true,
    autofillSkills: true,
    autofillExperience: true,
    autofillDemographic: false,
    autofillContact: true,
    askBeforeSensitiveFields: true,
    requireManualReview: true,
    confidenceThreshold: 80,
  });

  // Track changes
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

  // Original data for reset
  const [originalData, setOriginalData] = useState({
    skills,
    experiences,
    demographicData,
    autofillSettings,
  });

  useEffect(() => {
    setHasUnsavedChanges(true);
    setSaveStatus('idle');
  }, [skills, experiences, demographicData, autofillSettings]);

  const handleSave = async () => {
    setIsSaving(true);
    setSaveStatus('idle');

    // Simulate API call
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Update original data
      setOriginalData({
        skills,
        experiences,
        demographicData,
        autofillSettings,
      });

      setHasUnsavedChanges(false);
      setSaveStatus('success');

      // Clear success message after 3 seconds
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (error) {
      setSaveStatus('error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    if (hasUnsavedChanges) {
      if (!confirm('You have unsaved changes. Are you sure you want to cancel?')) {
        return;
      }
    }

    setSkills(originalData.skills);
    setExperiences(originalData.experiences);
    setDemographicData(originalData.demographicData);
    setAutofillSettings(originalData.autofillSettings);
    setHasUnsavedChanges(false);
    setSaveStatus('idle');
  };

  const handleReset = () => {
    if (!confirm('Reset all profile data to defaults? This cannot be undone.')) {
      return;
    }

    setSkills([]);
    setExperiences([]);
    setDemographicData({});
    setAutofillSettings({
      enabled: false,
      autofillSkills: false,
      autofillExperience: false,
      autofillDemographic: false,
      autofillContact: false,
      askBeforeSensitiveFields: true,
      requireManualReview: true,
      confidenceThreshold: 80,
    });
  };

  // Warn before leaving with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto pb-32">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-semibold text-foreground">Career Profile & Preferences</h1>
          <p className="mt-2 text-muted-foreground">
            Manage your professional profile, skills, and automation preferences. This data powers better job matching
            and helps autofill applications when you choose to enable it.
          </p>
        </div>

        <div className="space-y-6">
          {/* Skills Section */}
          <Card>
            <CardHeader>
              <CardTitle>Skills</CardTitle>
            </CardHeader>
            <CardContent>
              <SkillEditor skills={skills} onChange={setSkills} />
            </CardContent>
          </Card>

          {/* Experience Section */}
          <Card>
            <CardHeader>
              <CardTitle>Work Experience</CardTitle>
            </CardHeader>
            <CardContent>
              <ExperienceEditor experiences={experiences} onChange={setExperiences} />
            </CardContent>
          </Card>

          {/* Demographic Preferences */}
          <Card>
            <CardContent className="pt-6">
              <DemographicPreferences data={demographicData} onChange={setDemographicData} />
            </CardContent>
          </Card>

          {/* Autofill Controls */}
          <Card>
            <CardContent className="pt-6">
              <AutofillControls settings={autofillSettings} onChange={setAutofillSettings} />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Sticky Action Bar */}
      <div
        className={`fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur border-t border-border transition-transform duration-200 ${
          hasUnsavedChanges || saveStatus !== 'idle' ? 'translate-y-0' : 'translate-y-full'
        }`}
      >
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              {saveStatus === 'success' && (
                <div className="flex items-center gap-2 text-success">
                  <CheckCircle className="h-5 w-5" />
                  <span className="text-sm font-medium">Changes saved successfully</span>
                </div>
              )}
              {saveStatus === 'error' && (
                <div className="flex items-center gap-2 text-destructive">
                  <AlertCircle className="h-5 w-5" />
                  <span className="text-sm font-medium">Failed to save changes</span>
                </div>
              )}
              {hasUnsavedChanges && saveStatus === 'idle' && (
                <span className="text-sm text-muted-foreground">You have unsaved changes</span>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Button variant="ghost" onClick={handleReset} disabled={isSaving}>
                <RotateCcw className="h-4 w-4" />
                Reset All
              </Button>
              <Button variant="ghost" onClick={handleCancel} disabled={isSaving}>
                <X className="h-4 w-4" />
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleSave}
                loading={isSaving}
                disabled={!hasUnsavedChanges && saveStatus !== 'error'}
              >
                <Save className="h-4 w-4" />
                {saveStatus === 'error' ? 'Retry Save' : 'Save Changes'}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Action Bar */}
      <div
        className={`fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur border-t border-border md:hidden transition-transform duration-200 ${
          hasUnsavedChanges || saveStatus !== 'idle' ? 'translate-y-0' : 'translate-y-full'
        }`}
      >
        <div className="px-4 py-3 space-y-2">
          {saveStatus === 'success' && (
            <div className="flex items-center gap-2 text-success text-sm">
              <CheckCircle className="h-4 w-4" />
              <span>Changes saved</span>
            </div>
          )}
          {saveStatus === 'error' && (
            <div className="flex items-center gap-2 text-destructive text-sm">
              <AlertCircle className="h-4 w-4" />
              <span>Failed to save</span>
            </div>
          )}
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleCancel} fullWidth disabled={isSaving}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSave}
              fullWidth
              loading={isSaving}
              disabled={!hasUnsavedChanges && saveStatus !== 'error'}
            >
              Save
            </Button>
          </div>
        </div>
      </div>
    </AppShell>
  );
};
