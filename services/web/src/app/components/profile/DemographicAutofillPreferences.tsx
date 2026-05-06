import React from 'react';

export interface DemographicAutofillSettings {
  race: { value: string; autofill: boolean };
  gender: { value: string; autofill: boolean };
  veteranStatus: { value: string; autofill: boolean };
  disabilityStatus: { value: string; autofill: boolean };
  pronouns: { value: string; autofill: boolean };
}

interface DemographicAutofillPreferencesProps {
  settings: DemographicAutofillSettings;
  onChange: (settings: DemographicAutofillSettings) => void;
}

const RACE_OPTIONS = [
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

const YES_NO_OPTIONS = [
  'Select an option',
  'Yes',
  'No',
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

export const DemographicAutofillPreferences: React.FC<DemographicAutofillPreferencesProps> = ({
  settings,
  onChange,
}) => {
  const handleValueChange = (field: keyof DemographicAutofillSettings, value: string) => {
    onChange({
      ...settings,
      [field]: {
        ...settings[field],
        value: value === 'Select an option' ? '' : value,
      },
    });
  };

  const handleToggleChange = (field: keyof DemographicAutofillSettings, autofill: boolean) => {
    onChange({
      ...settings,
      [field]: {
        ...settings[field],
        autofill,
      },
    });
  };

  const DemographicRow = ({
    label,
    field,
    options,
  }: {
    label: string;
    field: keyof DemographicAutofillSettings;
    options: string[];
  }) => (
    <div className="flex items-start gap-4 pb-4 border-b border-border last:border-0 last:pb-0">
      <div className="flex-1">
        <label className="block text-sm font-medium text-foreground mb-2">{label}</label>
        <select
          value={settings[field].value || 'Select an option'}
          onChange={(e) => handleValueChange(field, e.target.value)}
          className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        >
          {options.map(option => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      </div>

      <div className="flex flex-col items-end pt-8">
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={settings[field].autofill}
            onChange={(e) => handleToggleChange(field, e.target.checked)}
            disabled={!settings[field].value}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-switch-background peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-ring rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand peer-disabled:opacity-50 peer-disabled:cursor-not-allowed"></div>
        </label>
        <span className="text-xs text-muted-foreground mt-1">
          {settings[field].autofill ? 'Autofill ON' : 'Autofill OFF'}
        </span>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-foreground mb-2">
          Demographic Autofill Preferences
        </h3>
        <p className="text-sm text-muted-foreground">
          Choose which demographic information to autofill in job applications. Toggle on to automatically
          fill these fields when detected.
        </p>
      </div>

      <div className="space-y-4">
        <DemographicRow label="Race/Ethnicity" field="race" options={RACE_OPTIONS} />
        <DemographicRow label="Gender" field="gender" options={GENDER_OPTIONS} />
        <DemographicRow label="Veteran Status" field="veteranStatus" options={YES_NO_OPTIONS} />
        <DemographicRow label="Disability Status" field="disabilityStatus" options={YES_NO_OPTIONS} />
        <DemographicRow label="Pronouns" field="pronouns" options={PRONOUN_OPTIONS} />
      </div>

      <div className="p-3 rounded-lg bg-muted/50 border border-border">
        <p className="text-xs text-muted-foreground">
          <strong>Privacy Note:</strong> This information is optional and only used to autofill application
          forms when you enable it. You maintain full control and can edit or skip any autofilled field.
        </p>
      </div>
    </div>
  );
};
