import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Edit, Trash2, Plus, Briefcase, X } from 'lucide-react';
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
  details: string[];
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
      details: [],
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
    const [activeDetailEditorIndex, setActiveDetailEditorIndex] = useState<number | null>(null);
    const [detailDraft, setDetailDraft] = useState('');
    const isEditing = editingId === experience.id;
    const isExpanded = expandedId === experience.id;

    const updateDetailAtIndex = (index: number, value: string) => {
      setLocalExp((prev) => ({
        ...prev,
        details: prev.details.map((detail, detailIndex) => (
          detailIndex === index ? value : detail
        )),
      }));
    };

    const addDetailBullet = () => {
      const newDetailIndex = localExp.details.length;
      setLocalExp((prev) => ({
        ...prev,
        details: [...prev.details, ''],
      }));
      setActiveDetailEditorIndex(newDetailIndex);
      setDetailDraft('');
    };

    const removeDetailAtIndex = (index: number) => {
      setLocalExp((prev) => ({
        ...prev,
        details: prev.details.filter((_, detailIndex) => detailIndex !== index),
      }));
      setActiveDetailEditorIndex((prevIndex) => {
        if (prevIndex === null) {
          return prevIndex;
        }
        if (prevIndex === index) {
          return null;
        }
        if (prevIndex > index) {
          return prevIndex - 1;
        }
        return prevIndex;
      });
    };

    const startDetailEditing = (index: number) => {
      setActiveDetailEditorIndex(index);
      setDetailDraft(localExp.details[index] ?? '');
    };

    const cancelDetailEditing = () => {
      setActiveDetailEditorIndex(null);
      setDetailDraft('');
    };

    const saveDetailEditing = () => {
      if (activeDetailEditorIndex === null) {
        return;
      }

      const sanitizedDraft = detailDraft.trim();
      const nextLocalExp = {
        ...localExp,
        details: localExp.details.map((detail, detailIndex) => (
          detailIndex === activeDetailEditorIndex ? sanitizedDraft : detail
        )),
      };

      setLocalExp(nextLocalExp);
      onChange(experiences.map((exp) => (exp.id === nextLocalExp.id ? nextLocalExp : exp)));

      setActiveDetailEditorIndex(null);
      setDetailDraft('');
    };

    const sanitizeDetails = (details: string[]) => (
      details
        .map((detail) => detail.trim())
        .filter((detail) => detail.length > 0)
    );

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
              onClick={() => handleSave({
                ...localExp,
                details: sanitizeDetails(localExp.details),
              })}
              disabled={!localExp.role || !localExp.company}
            >
              Save
            </Button>
          </div>

          <div className="space-y-3 pt-2 border-t border-border">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-foreground">Detail Bullet Points</p>
              <Button variant="outline" size="sm" onClick={addDetailBullet}>
                <Plus className="h-4 w-4" />
                Add Bullet
              </Button>
            </div>

            {localExp.details.length > 0 ? (
              <div className="space-y-2">
                {localExp.details.map((detail, index) => (
                  <div key={`${experience.id}-edit-detail-${index}`} className="rounded-lg border border-border p-3 space-y-3">
                    {activeDetailEditorIndex !== index ? (
                      <div className="flex items-start gap-2">
                        <p className="flex-1 text-sm text-foreground break-words">
                          <span className="text-muted-foreground mr-2">•</span>
                          {detail.trim() || 'Empty bullet point'}
                        </p>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => startDetailEditing(index)}
                            aria-label={`Edit detail bullet ${index + 1}`}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeDetailAtIndex(index)}
                            aria-label={`Remove detail bullet ${index + 1}`}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex justify-end">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeDetailAtIndex(index)}
                          aria-label={`Remove detail bullet ${index + 1}`}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    )}

                    {activeDetailEditorIndex === index ? (
                      <div className="space-y-2">
                        <textarea
                          value={detailDraft}
                          onChange={(event) => setDetailDraft(event.target.value)}
                          placeholder="Describe a key achievement or responsibility"
                          className="w-full min-h-[110px] resize-y px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                        />
                        <div className="flex justify-end gap-2">
                          <Button variant="ghost" size="sm" onClick={cancelDetailEditing}>
                            Cancel
                          </Button>
                          <Button variant="primary" size="sm" onClick={saveDetailEditing}>
                            Apply
                          </Button>
                        </div>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No bullet points yet. Add one to capture impact.</p>
            )}
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
              {experience.details.length > 0 ? (
                <ul className="list-disc pl-5 space-y-2">
                  {experience.details.map((detail, index) => (
                    <li key={`${experience.id}-detail-${index}`} className="text-sm text-muted-foreground">
                      {detail}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">No additional details provided.</p>
              )}
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
