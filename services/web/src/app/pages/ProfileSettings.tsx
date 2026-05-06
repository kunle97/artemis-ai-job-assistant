import React, { useState } from 'react';
import { AppShell } from '../components/AppShell';
import { Button, Card, CardHeader, CardTitle, CardContent, Input } from '../components/ui';
import { Save, CheckCircle } from 'lucide-react';

export const ProfileSettings: React.FC = () => {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [formData, setFormData] = useState({
    fullName: 'John Doe',
    email: 'john@example.com',
    phone: '+1 (555) 123-4567',
    location: 'San Francisco, CA',
    linkedin: 'https://linkedin.com/in/johndoe',
    portfolio: 'https://johndoe.com',
    github: 'https://github.com/johndoe',
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
              <h1 className="text-3xl font-semibold text-foreground">Candidate Profile</h1>
              <p className="mt-2 text-muted-foreground">Manage your personal information and professional links</p>
            </div>
            {saved && (
              <div className="flex items-center gap-2 text-success">
                <CheckCircle className="h-5 w-5" />
                <span className="font-medium">Changes saved</span>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          {/* Personal Information */}
          <Card>
            <CardHeader>
              <CardTitle>Personal Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Full Name"
                  value={formData.fullName}
                  onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                  fullWidth
                />
                <Input
                  label="Email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  fullWidth
                />
                <Input
                  label="Phone"
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  fullWidth
                />
                <Input
                  label="Location"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  fullWidth
                />
              </div>
            </CardContent>
          </Card>

          {/* Professional Links */}
          <Card>
            <CardHeader>
              <CardTitle>Professional Links</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                label="LinkedIn Profile"
                value={formData.linkedin}
                onChange={(e) => setFormData({ ...formData, linkedin: e.target.value })}
                fullWidth
                placeholder="https://linkedin.com/in/yourprofile"
              />
              <Input
                label="Portfolio Website"
                value={formData.portfolio}
                onChange={(e) => setFormData({ ...formData, portfolio: e.target.value })}
                fullWidth
                placeholder="https://yourwebsite.com"
              />
              <Input
                label="GitHub Profile"
                value={formData.github}
                onChange={(e) => setFormData({ ...formData, github: e.target.value })}
                fullWidth
                placeholder="https://github.com/yourusername"
              />
            </CardContent>
          </Card>

          {/* Automation Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Automation Preferences</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <label className="flex items-start gap-3 cursor-pointer">
                <input type="checkbox" defaultChecked className="h-5 w-5 rounded border-border text-brand mt-0.5" />
                <div>
                  <p className="font-medium text-foreground">Auto-fill from resume</p>
                  <p className="text-sm text-muted-foreground">
                    Automatically use resume data when available
                  </p>
                </div>
              </label>
              <label className="flex items-start gap-3 cursor-pointer">
                <input type="checkbox" defaultChecked className="h-5 w-5 rounded border-border text-brand mt-0.5" />
                <div>
                  <p className="font-medium text-foreground">Match saved answers</p>
                  <p className="text-sm text-muted-foreground">
                    Use your answers library to fill application questions
                  </p>
                </div>
              </label>
              <label className="flex items-start gap-3 cursor-pointer">
                <input type="checkbox" className="h-5 w-5 rounded border-border text-brand mt-0.5" />
                <div>
                  <p className="font-medium text-foreground">Skip manual review</p>
                  <p className="text-sm text-muted-foreground">
                    Proceed to authorization without manual review (not recommended)
                  </p>
                </div>
              </label>
            </CardContent>
          </Card>

          {/* Save Button */}
          <div className="flex justify-end">
            <Button variant="primary" size="lg" onClick={handleSave} loading={saving}>
              <Save className="h-4 w-4" />
              Save Changes
            </Button>
          </div>
        </div>
      </div>
    </AppShell>
  );
};
