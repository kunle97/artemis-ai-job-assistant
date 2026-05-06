import React from 'react';
import { Zap, AlertTriangle, Shield, Info } from 'lucide-react';

export interface AutofillSettings {
  enabled: boolean;
  autofillSkills: boolean;
  autofillExperience: boolean;
  autofillDemographic: boolean;
  autofillContact: boolean;
  askBeforeSensitiveFields: boolean;
  requireManualReview: boolean;
  confidenceThreshold: number;
}

interface AutofillControlsProps {
  settings: AutofillSettings;
  onChange: (settings: AutofillSettings) => void;
}

export const AutofillControls: React.FC<AutofillControlsProps> = ({ settings, onChange }) => {
  const handleToggle = (field: keyof AutofillSettings, value: boolean) => {
    const newSettings = { ...settings, [field]: value };

    // If disabling master toggle, disable all sub-toggles
    if (field === 'enabled' && !value) {
      newSettings.autofillSkills = false;
      newSettings.autofillExperience = false;
      newSettings.autofillDemographic = false;
      newSettings.autofillContact = false;
    }

    onChange(newSettings);
  };

  const handleThresholdChange = (value: number) => {
    onChange({ ...settings, confidenceThreshold: value });
  };

  const isRiskyConfiguration = settings.enabled &&
    !settings.requireManualReview &&
    !settings.askBeforeSensitiveFields;

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3">
        <div className="h-10 w-10 rounded-full bg-brand/10 flex items-center justify-center flex-shrink-0">
          <Zap className="h-5 w-5 text-brand" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Autofill Controls
          </h3>
          <p className="text-sm text-muted-foreground">
            Configure how Artemis assists with filling out job applications. You remain in control of every submission.
          </p>
        </div>
      </div>

      {/* Master Toggle */}
      <div className="p-4 border-2 border-brand/20 rounded-lg bg-brand/5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h4 className="font-semibold text-foreground mb-1">Enable Autofill Assistance</h4>
            <p className="text-sm text-muted-foreground">
              Allow Artemis to suggest answers based on your profile data
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.enabled}
              onChange={(e) => handleToggle('enabled', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-switch-background peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-ring rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand"></div>
          </label>
        </div>
      </div>

      {/* Granular Controls */}
      {settings.enabled && (
        <>
          <div className="space-y-3 pl-4 border-l-2 border-border">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h4 className="font-medium text-foreground mb-1">Autofill Skills</h4>
                <p className="text-sm text-muted-foreground">
                  Auto-populate skill questions from your profile
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.autofillSkills}
                  onChange={(e) => handleToggle('autofillSkills', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-switch-background peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-ring rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand"></div>
              </label>
            </div>

            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h4 className="font-medium text-foreground mb-1">Autofill Experience</h4>
                <p className="text-sm text-muted-foreground">
                  Auto-populate work history from your experience entries
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.autofillExperience}
                  onChange={(e) => handleToggle('autofillExperience', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-switch-background peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-ring rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand"></div>
              </label>
            </div>

            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h4 className="font-medium text-foreground mb-1 flex items-center gap-2">
                  Autofill Demographic Data
                  <Shield className="h-4 w-4 text-muted-foreground" />
                </h4>
                <p className="text-sm text-muted-foreground">
                  Pre-fill optional demographic questions (never shared without consent)
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.autofillDemographic}
                  onChange={(e) => handleToggle('autofillDemographic', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-switch-background peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-ring rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand"></div>
              </label>
            </div>

            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h4 className="font-medium text-foreground mb-1">Autofill Contact Info</h4>
                <p className="text-sm text-muted-foreground">
                  Pre-fill email, phone, and address fields
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.autofillContact}
                  onChange={(e) => handleToggle('autofillContact', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-switch-background peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-ring rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand"></div>
              </label>
            </div>
          </div>

          {/* Safety Controls */}
          <div className="space-y-3 p-4 rounded-lg bg-muted/30 border border-border">
            <h4 className="font-semibold text-foreground mb-2">Safety Controls</h4>

            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.askBeforeSensitiveFields}
                onChange={(e) => handleToggle('askBeforeSensitiveFields', e.target.checked)}
                className="mt-1 h-4 w-4 rounded border-border text-brand"
              />
              <div className="flex-1">
                <span className="text-sm font-medium text-foreground">Ask before filling sensitive fields</span>
                <p className="text-sm text-muted-foreground">
                  Artemis will prompt you before auto-filling demographic or salary-related questions
                </p>
              </div>
            </label>

            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.requireManualReview}
                onChange={(e) => handleToggle('requireManualReview', e.target.checked)}
                className="mt-1 h-4 w-4 rounded border-border text-brand"
              />
              <div className="flex-1">
                <span className="text-sm font-medium text-foreground">Always require manual review before submit</span>
                <p className="text-sm text-muted-foreground">
                  You must review and approve every application before Artemis can submit it
                </p>
              </div>
            </label>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Answer Confidence Threshold
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={settings.confidenceThreshold}
                  onChange={(e) => handleThresholdChange(parseInt(e.target.value))}
                  className="flex-1"
                />
                <span className="text-sm font-medium text-foreground w-12 text-right">
                  {settings.confidenceThreshold}%
                </span>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                Artemis will only suggest answers when it's at least {settings.confidenceThreshold}% confident
              </p>
            </div>
          </div>

          {/* Risk Warning */}
          {isRiskyConfiguration && (
            <div className="p-4 rounded-lg bg-warning/10 border border-warning/20 flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-warning flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground mb-1">Review Recommended</p>
                <p className="text-sm text-muted-foreground">
                  You've disabled manual review and sensitive field warnings. We strongly recommend enabling at least
                  one safety control to maintain full control over your applications.
                </p>
              </div>
            </div>
          )}
        </>
      )}

      {/* Info Banner */}
      <div className="p-3 rounded-lg bg-info/10 border border-info/20 flex items-start gap-3">
        <Info className="h-5 w-5 text-info flex-shrink-0 mt-0.5" />
        <p className="text-sm text-foreground">
          <strong>You're always in control.</strong> Autofill is a convenience feature. You can edit, skip, or
          disable any suggestion at any time. Artemis never submits applications without your explicit approval.
        </p>
      </div>
    </div>
  );
};
