import React from 'react';
import { Shield, Info } from 'lucide-react';

export interface DemographicData {
  workAuthorization?: string;
  veteranStatus?: string;
  disabilityStatus?: string;
  genderIdentity?: string;
  pronouns?: string;
  ethnicity?: string;
}

interface DemographicPreferencesProps {
  data: DemographicData;
  onChange: (data: DemographicData) => void;
}

const WORK_AUTH_OPTIONS = [
  'Select an option',
  'US Citizen',
  'Permanent Resident',
  'Work Visa (H1B, etc.)',
  'Require Sponsorship',
  'Prefer not to say',
];

const VETERAN_OPTIONS = [
  'Select an option',
  'Yes',
  'No',
  'Prefer not to say',
];

const DISABILITY_OPTIONS = [
  'Select an option',
  'Yes',
  'No',
  'Prefer not to say',
];

const GENDER_OPTIONS = [
  'Select an option',
  'Man',
  'Woman',
  'Non-binary',
  'Transgender',
  'Genderqueer',
  'Agender',
  'Self-describe',
  'Prefer not to say',
];

const PRONOUN_OPTIONS = [
  'Select an option',
  'he/him',
  'she/her',
  'they/them',
  'he/they',
  'she/they',
  'Other',
  'Prefer not to say',
];

const ETHNICITY_OPTIONS = [
  'Select an option',
  'Asian',
  'Black or African American',
  'Hispanic or Latino',
  'Middle Eastern or North African',
  'Native American or Alaska Native',
  'Native Hawaiian or Pacific Islander',
  'White',
  'Two or more races',
  'Prefer not to say',
];

export const DemographicPreferences: React.FC<DemographicPreferencesProps> = ({
  data,
  onChange,
}) => {
  const handleChange = (field: keyof DemographicData, value: string) => {
    onChange({
      ...data,
      [field]: value === 'Select an option' ? undefined : value,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3">
        <div className="h-10 w-10 rounded-full bg-brand/10 flex items-center justify-center flex-shrink-0">
          <Shield className="h-5 w-5 text-brand" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Demographic Preferences
          </h3>
          <p className="text-sm text-muted-foreground">
            This information is completely optional and helps personalize recommendations. You can skip any field or select
            "Prefer not to say" at any time. We never share this data without your explicit consent.
          </p>
        </div>
      </div>

      {/* Privacy Notice */}
      <div className="p-4 rounded-lg bg-info/10 border border-info/20 flex items-start gap-3">
        <Info className="h-5 w-5 text-info flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="text-sm text-foreground">
            <strong>Your privacy is protected.</strong> Demographic data is stored separately and only used to
            improve job recommendations and pre-fill optional application fields when you explicitly allow it.
          </p>
          <button className="text-sm text-brand hover:underline mt-1">
            Learn more about our privacy practices →
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {/* Work Authorization */}
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Work Authorization <span className="text-muted-foreground font-normal">(Optional)</span>
          </label>
          <select
            value={data.workAuthorization || 'Select an option'}
            onChange={(e) => handleChange('workAuthorization', e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {WORK_AUTH_OPTIONS.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </div>

        {/* Veteran Status */}
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Veteran Status <span className="text-muted-foreground font-normal">(Optional)</span>
          </label>
          <select
            value={data.veteranStatus || 'Select an option'}
            onChange={(e) => handleChange('veteranStatus', e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {VETERAN_OPTIONS.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </div>

        {/* Disability Status */}
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Disability Disclosure <span className="text-muted-foreground font-normal">(Optional)</span>
          </label>
          <select
            value={data.disabilityStatus || 'Select an option'}
            onChange={(e) => handleChange('disabilityStatus', e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {DISABILITY_OPTIONS.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
          <p className="text-xs text-muted-foreground mt-1">
            Some employers are required to collect this information for legal compliance
          </p>
        </div>

        {/* Gender Identity */}
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Gender Identity <span className="text-muted-foreground font-normal">(Optional)</span>
          </label>
          <select
            value={data.genderIdentity || 'Select an option'}
            onChange={(e) => handleChange('genderIdentity', e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {GENDER_OPTIONS.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </div>

        {/* Pronouns */}
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Pronouns <span className="text-muted-foreground font-normal">(Optional)</span>
          </label>
          <select
            value={data.pronouns || 'Select an option'}
            onChange={(e) => handleChange('pronouns', e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {PRONOUN_OPTIONS.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </div>

        {/* Ethnicity */}
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Race/Ethnicity <span className="text-muted-foreground font-normal">(Optional)</span>
          </label>
          <select
            value={data.ethnicity || 'Select an option'}
            onChange={(e) => handleChange('ethnicity', e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {ETHNICITY_OPTIONS.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="p-3 rounded-lg bg-muted/50 border border-border">
        <p className="text-xs text-muted-foreground">
          <strong>Note:</strong> You can change or remove this information at any time. Artemis will never use this
          data to filter or limit opportunities shown to you.
        </p>
      </div>
    </div>
  );
};
