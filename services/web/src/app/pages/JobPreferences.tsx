'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '../components/AppShell';
import { Button, Card, CardHeader, CardTitle, CardContent, Input } from '../components/ui';
import { DemographicAutofillPreferences, DemographicAutofillSettings } from '../components/profile/DemographicAutofillPreferences';
import { Save, CheckCircle, Sparkles } from 'lucide-react';

export const JobPreferences: React.FC = () => {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [formData, setFormData] = useState({
    jobTitles: 'Product Manager, Senior Product Manager, Director of Product',
    keywords: 'B2B SaaS, product strategy, roadmap, user research',
    minSalary: '150000',
    maxSalary: '200000',
    locations: 'San Francisco, Remote, New York',
  });

  const [workModes, setWorkModes] = useState({
    remote: true,
    hybrid: true,
    onsite: false,
  });

  const [jobTypes, setJobTypes] = useState({
    fullTime: true,
    partTime: false,
    contract: false,
  });

  const [demographicSettings, setDemographicSettings] = useState<DemographicAutofillSettings>({
    race: { value: '', autofill: false },
    gender: { value: '', autofill: false },
    veteranStatus: { value: '', autofill: false },
    disabilityStatus: { value: '', autofill: false },
    pronouns: { value: '', autofill: false },
  });

  const handleSave = () => {
    setSaving(true);
    setSaved(false);
    setTimeout(() => {
      setSaving(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    }, 1000);
  };

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-semibold text-foreground">Job Preferences</h1>
              <p className="mt-2 text-muted-foreground">
                Configure your job search criteria to get better-matched opportunities
              </p>
            </div>
            {saved && (
              <div className="flex items-center gap-2 text-success">
                <CheckCircle className="h-5 w-5" />
                <span className="font-medium">Preferences saved</span>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          {/* Role Targeting */}
          <Card>
            <CardHeader>
              <CardTitle>Role Targeting</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                label="Target Job Titles"
                value={formData.jobTitles}
                onChange={(e) => setFormData({ ...formData, jobTitles: e.target.value })}
                fullWidth
                helperText="Separate multiple titles with commas"
                placeholder="e.g., Product Manager, Senior Product Manager"
              />
              <Input
                label="Keywords"
                value={formData.keywords}
                onChange={(e) => setFormData({ ...formData, keywords: e.target.value })}
                fullWidth
                helperText="Skills, technologies, or domains you're interested in"
                placeholder="e.g., B2B SaaS, AI/ML, fintech"
              />
            </CardContent>
          </Card>

          {/* Work Mode */}
          <Card>
            <CardHeader>
              <CardTitle>Work Mode Preferences</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={workModes.remote}
                  onChange={(e) => setWorkModes({ ...workModes, remote: e.target.checked })}
                  className="h-5 w-5 rounded border-border text-brand"
                />
                <div>
                  <p className="font-medium text-foreground">Remote</p>
                  <p className="text-sm text-muted-foreground">Work from anywhere</p>
                </div>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={workModes.hybrid}
                  onChange={(e) => setWorkModes({ ...workModes, hybrid: e.target.checked })}
                  className="h-5 w-5 rounded border-border text-brand"
                />
                <div>
                  <p className="font-medium text-foreground">Hybrid</p>
                  <p className="text-sm text-muted-foreground">Mix of remote and in-office</p>
                </div>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={workModes.onsite}
                  onChange={(e) => setWorkModes({ ...workModes, onsite: e.target.checked })}
                  className="h-5 w-5 rounded border-border text-brand"
                />
                <div>
                  <p className="font-medium text-foreground">On-site</p>
                  <p className="text-sm text-muted-foreground">Full-time in-office</p>
                </div>
              </label>
            </CardContent>
          </Card>

          {/* Employment Type */}
          <Card>
            <CardHeader>
              <CardTitle>Employment Type</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={jobTypes.fullTime}
                  onChange={(e) => setJobTypes({ ...jobTypes, fullTime: e.target.checked })}
                  className="h-5 w-5 rounded border-border text-brand"
                />
                <div>
                  <p className="font-medium text-foreground">Full-time</p>
                </div>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={jobTypes.partTime}
                  onChange={(e) => setJobTypes({ ...jobTypes, partTime: e.target.checked })}
                  className="h-5 w-5 rounded border-border text-brand"
                />
                <div>
                  <p className="font-medium text-foreground">Part-time</p>
                </div>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={jobTypes.contract}
                  onChange={(e) => setJobTypes({ ...jobTypes, contract: e.target.checked })}
                  className="h-5 w-5 rounded border-border text-brand"
                />
                <div>
                  <p className="font-medium text-foreground">Contract</p>
                </div>
              </label>
            </CardContent>
          </Card>

          {/* Compensation */}
          <Card>
            <CardHeader>
              <CardTitle>Compensation Expectations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Minimum Salary"
                  type="number"
                  value={formData.minSalary}
                  onChange={(e) => setFormData({ ...formData, minSalary: e.target.value })}
                  fullWidth
                  placeholder="150000"
                />
                <Input
                  label="Maximum Salary"
                  type="number"
                  value={formData.maxSalary}
                  onChange={(e) => setFormData({ ...formData, maxSalary: e.target.value })}
                  fullWidth
                  placeholder="200000"
                />
              </div>
              <p className="text-sm text-muted-foreground">
                These values help filter your job feed but won't be shared with employers without your consent
              </p>
            </CardContent>
          </Card>

          {/* Locations */}
          <Card>
            <CardHeader>
              <CardTitle>Preferred Locations</CardTitle>
            </CardHeader>
            <CardContent>
              <Input
                label="Locations"
                value={formData.locations}
                onChange={(e) => setFormData({ ...formData, locations: e.target.value })}
                fullWidth
                helperText="Separate multiple locations with commas. Use 'Remote' for remote-only positions"
                placeholder="e.g., San Francisco, New York, Remote"
              />
            </CardContent>
          </Card>

          {/* Demographic Autofill Preferences */}
          <Card>
            <CardContent className="pt-6">
              <DemographicAutofillPreferences
                settings={demographicSettings}
                onChange={setDemographicSettings}
              />
            </CardContent>
          </Card>

          {/* Impact Preview */}
          <Card variant="outlined" className="bg-brand/5 border-brand/20">
            <CardContent className="pt-6">
              <div className="flex gap-3">
                <Sparkles className="h-5 w-5 text-brand flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-foreground mb-1">How this affects your feed</p>
                  <p className="text-sm text-muted-foreground">
                    Artemis uses these preferences to score and filter job opportunities. More specific preferences lead to better matches but may reduce the number of results. You can always adjust these settings based on what you're seeing.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Save Button */}
          <div className="flex justify-end gap-3">
            <Button variant="outline" size="lg" onClick={() => router.push('/jobs')}>
              Cancel
            </Button>
            <Button variant="primary" size="lg" onClick={handleSave} loading={saving}>
              <Save className="h-4 w-4" />
              Save Preferences
            </Button>
          </div>
        </div>
      </div>
    </AppShell>
  );
};
