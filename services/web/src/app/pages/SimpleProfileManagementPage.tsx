import React, { useState } from 'react';
import { AppShell } from '../components/AppShell';
import { Button, Card, CardHeader, CardTitle, CardContent } from '../components/ui';
import { SimpleSkillEditor, SimpleSkill } from '../components/profile/SimpleSkillEditor';
import { SimpleExperienceEditor, SimpleExperience } from '../components/profile/SimpleExperienceEditor';
import { Save, X, CheckCircle, AlertCircle } from 'lucide-react';

export const SimpleProfileManagementPage: React.FC = () => {
  const [skills, setSkills] = useState<SimpleSkill[]>([
    { id: '1', name: 'JavaScript' },
    { id: '2', name: 'React' },
    { id: '3', name: 'TypeScript' },
  ]);

  const [experiences, setExperiences] = useState<SimpleExperience[]>([
    {
      id: '1',
      role: 'Senior Software Engineer',
      company: 'TechCorp',
      startMonth: 'June',
      startYear: '2021',
      endMonth: '',
      endYear: '',
      currentlyWorking: true,
    },
  ]);

  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

  // Track changes
  React.useEffect(() => {
    setHasUnsavedChanges(true);
    setSaveStatus('idle');
  }, [skills, experiences]);

  const handleSave = async () => {
    setIsSaving(true);
    setSaveStatus('idle');

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));

    setHasUnsavedChanges(false);
    setSaveStatus('success');
    setIsSaving(false);

    // Clear success message after 3 seconds
    setTimeout(() => setSaveStatus('idle'), 3000);
  };

  const handleCancel = () => {
    if (hasUnsavedChanges && !confirm('Discard unsaved changes?')) {
      return;
    }
    setHasUnsavedChanges(false);
    setSaveStatus('idle');
  };

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto pb-32">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-semibold text-foreground">My Career</h1>
          <p className="mt-2 text-muted-foreground">
            Manage your skills and work experience for job applications.
          </p>
        </div>

        <div className="space-y-6">
          {/* Skills Section */}
          <Card>
            <CardHeader>
              <CardTitle>Skills</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Add your professional skills. These will appear as removable tags.
              </p>
            </CardHeader>
            <CardContent>
              <SimpleSkillEditor skills={skills} onChange={setSkills} />
            </CardContent>
          </Card>

          {/* Experience Section */}
          <Card>
            <CardContent className="pt-6">
              <SimpleExperienceEditor experiences={experiences} onChange={setExperiences} />
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
