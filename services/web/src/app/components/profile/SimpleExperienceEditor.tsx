import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Edit, Trash2, Plus, Briefcase } from 'lucide-react';
import { Button, Input } from '../ui';

export interface SimpleExperience {
  id: string;
  role: string;
  company: string;
  startMonth: string;
  startYear: string;
  endMonth: string;
  endYear: string;
  currentlyWorking: boolean;
}

interface SimpleExperienceEditorProps {
  experiences: SimpleExperience[];
  onChange: (experiences: SimpleExperience[]) => void;
}

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const YEARS = Array.from({ length: 50 }, (_, i) => (new Date().getFullYear() - i).toString());

export const SimpleExperienceEditor: React.FC<SimpleExperienceEditorProps> = ({
  experiences,
  onChange,
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const handleAdd = () => {
    const newExp: SimpleExperience = {
      id: Date.now().toString(),
      role: '',
      company: '',
      startMonth: '',
      startYear: '',
      endMonth: '',
      endYear: '',
      currentlyWorking: false,
    };
    onChange([newExp, ...experiences]);
    setEditingId(newExp.id);
  };

  const handleSave = (exp: SimpleExperience) => {
    onChange(experiences.map(e => e.id === exp.id ? exp : e));
    setEditingId(null);
  };

  const handleCancel = (id: string) => {
    const exp = experiences.find(e => e.id === id);
    if (exp && !exp.role && !exp.company) {
      onChange(experiences.filter(e => e.id !== id));
    }
    setEditingId(null);
  };

  const handleDelete = (id: string) => {
    if (confirm('Delete this experience?')) {
      onChange(experiences.filter(e => e.id !== id));
    }
  };

  const ExperienceCard = ({ experience }: { experience: SimpleExperience }) => {
    const [localExp, setLocalExp] = useState(experience);
    const isEditing = editingId === experience.id;
    const isExpanded = expandedId === experience.id;

    if (isEditing) {
      return (
        <div className="p-4 border-2 border-brand rounded-lg bg-background space-y-4">
          <h4 className="text-sm font-medium text-foreground">
            {experience.role ? 'Edit Experience' : 'Add New Experience'}
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Job Title"
              value={localExp.role}
              onChange={(e) => setLocalExp({ ...localExp, role: e.target.value })}
              placeholder="e.g., Software Engineer"
              required
            />
            <Input
              label="Company"
              value={localExp.company}
              onChange={(e) => setLocalExp({ ...localExp, company: e.target.value })}
              placeholder="e.g., TechCorp"
              required
            />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Start Month</label>
              <select
                value={localExp.startMonth}
                onChange={(e) => setLocalExp({ ...localExp, startMonth: e.target.value })}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">Select</option>
                {MONTHS.map(month => (
                  <option key={month} value={month}>{month}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Start Year</label>
              <select
                value={localExp.startYear}
                onChange={(e) => setLocalExp({ ...localExp, startYear: e.target.value })}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">Select</option>
                {YEARS.map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">End Month</label>
              <select
                value={localExp.endMonth}
                onChange={(e) => setLocalExp({ ...localExp, endMonth: e.target.value, currentlyWorking: false })}
                disabled={localExp.currentlyWorking}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
              >
                <option value="">Select</option>
                {MONTHS.map(month => (
                  <option key={month} value={month}>{month}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">End Year</label>
              <select
                value={localExp.endYear}
                onChange={(e) => setLocalExp({ ...localExp, endYear: e.target.value, currentlyWorking: false })}
                disabled={localExp.currentlyWorking}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
              >
                <option value="">Select</option>
                {YEARS.map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>
          </div>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={localExp.currentlyWorking}
              onChange={(e) => setLocalExp({
                ...localExp,
                currentlyWorking: e.target.checked,
                endMonth: e.target.checked ? '' : localExp.endMonth,
                endYear: e.target.checked ? '' : localExp.endYear
              })}
              className="h-4 w-4 rounded border-border text-brand"
            />
            <span className="text-sm text-foreground">I currently work here</span>
          </label>

          <div className="flex gap-2 justify-end">
            <Button variant="ghost" onClick={() => handleCancel(experience.id)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => handleSave(localExp)}
              disabled={!localExp.role || !localExp.company}
            >
              Save
            </Button>
          </div>
        </div>
      );
    }

    const roleText = experience.role?.trim() || 'Untitled role';
    const companyText = experience.company?.trim() || 'Company not specified';

    const startDate = [experience.startMonth, experience.startYear]
      .map((value) => value?.trim())
      .filter(Boolean)
      .join(' ');
    const endDate = experience.currentlyWorking
      ? 'Present'
      : [experience.endMonth, experience.endYear]
        .map((value) => value?.trim())
        .filter(Boolean)
        .join(' ');
    const dateRange = `${startDate || 'Start date not specified'} - ${endDate || 'End date not specified'}`;

    return (
      <div className="border border-border rounded-lg bg-background">
        <div className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-foreground">{roleText}</h3>
              <p className="text-sm text-muted-foreground">{companyText}</p>
              <p className="text-sm text-muted-foreground mt-1">{dateRange}</p>
            </div>

            <div className="flex items-center gap-1 ml-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setEditingId(experience.id)}
              >
                <Edit className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDelete(experience.id)}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setExpandedId(isExpanded ? null : experience.id)}
              >
                {isExpanded ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          {isExpanded && (
            <div className="mt-4 pt-4 border-t border-border">
              <p className="text-sm text-muted-foreground">
                Additional details can be displayed here when expanded.
              </p>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-foreground">Work Experience</h3>
        <Button variant="outline" onClick={handleAdd}>
          <Plus className="h-4 w-4" />
          Add Experience
        </Button>
      </div>

      {experiences.length > 0 ? (
        <div className="space-y-3">
          {experiences.map((exp, index) => (
            <ExperienceCard key={exp.id || `experience-${index}`} experience={exp} />
          ))}
        </div>
      ) : (
        <div className="p-12 text-center border border-dashed border-border rounded-lg bg-muted/20">
          <Briefcase className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
          <p className="text-muted-foreground mb-4">No work experience added yet</p>
          <Button variant="primary" onClick={handleAdd}>
            <Plus className="h-4 w-4" />
            Add Your First Experience
          </Button>
        </div>
      )}
    </div>
  );
};
