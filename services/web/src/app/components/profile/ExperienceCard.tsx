import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Edit, Trash2, GripVertical } from 'lucide-react';
import { Button, Input } from '../ui';

export interface Experience {
  id: string;
  role: string;
  company: string;
  startDate: string;
  endDate: string | null;
  currentlyWorking: boolean;
  location: string;
  summary: string;
}

interface ExperienceCardProps {
  experience: Experience;
  onEdit: (experience: Experience) => void;
  onDelete: (id: string) => void;
  isEditing?: boolean;
  onSave?: (experience: Experience) => void;
  onCancelEdit?: () => void;
  hasUnsavedChanges?: boolean;
}

export const ExperienceCard: React.FC<ExperienceCardProps> = ({
  experience,
  onEdit,
  onDelete,
  isEditing = false,
  onSave,
  onCancelEdit,
  hasUnsavedChanges = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [editedExperience, setEditedExperience] = useState(experience);

  const handleSave = () => {
    if (onSave) {
      onSave(editedExperience);
    }
  };

  const formatDateRange = () => {
    const start = new Date(experience.startDate).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    const end = experience.currentlyWorking
      ? 'Present'
      : new Date(experience.endDate!).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    return `${start} - ${end}`;
  };

  if (isEditing) {
    return (
      <div className="p-4 border-2 border-brand rounded-lg bg-background space-y-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-foreground">Edit Experience</h4>
          {hasUnsavedChanges && (
            <span className="text-xs text-warning">Unsaved changes</span>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Role Title"
            value={editedExperience.role}
            onChange={(e) => setEditedExperience({ ...editedExperience, role: e.target.value })}
            required
          />
          <Input
            label="Company"
            value={editedExperience.company}
            onChange={(e) => setEditedExperience({ ...editedExperience, company: e.target.value })}
            required
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Input
            label="Start Date"
            type="month"
            value={editedExperience.startDate}
            onChange={(e) => setEditedExperience({ ...editedExperience, startDate: e.target.value })}
            required
          />
          <Input
            label="End Date"
            type="month"
            value={editedExperience.endDate || ''}
            onChange={(e) => setEditedExperience({ ...editedExperience, endDate: e.target.value, currentlyWorking: false })}
            disabled={editedExperience.currentlyWorking}
          />
          <div className="flex items-end pb-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={editedExperience.currentlyWorking}
                onChange={(e) => setEditedExperience({
                  ...editedExperience,
                  currentlyWorking: e.target.checked,
                  endDate: e.target.checked ? null : editedExperience.endDate
                })}
                className="h-4 w-4 rounded border-border text-brand"
              />
              <span className="text-sm text-foreground">Currently working here</span>
            </label>
          </div>
        </div>

        <Input
          label="Location"
          value={editedExperience.location}
          onChange={(e) => setEditedExperience({ ...editedExperience, location: e.target.value })}
          placeholder="e.g., San Francisco, CA or Remote"
        />

        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Summary
          </label>
          <textarea
            value={editedExperience.summary}
            onChange={(e) => setEditedExperience({ ...editedExperience, summary: e.target.value })}
            rows={4}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none"
            placeholder="Describe your role, achievements, and impact..."
          />
          <p className="text-xs text-muted-foreground mt-1">
            Use bullet points to highlight key achievements and responsibilities
          </p>
        </div>

        <div className="flex gap-2 justify-end pt-2">
          <Button variant="ghost" onClick={onCancelEdit}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSave}>
            Save Changes
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="border border-border rounded-lg bg-background hover:border-border/60 transition-colors">
      {/* Collapsed Header */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          <button
            className="mt-1 cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground"
            aria-label="Drag to reorder"
          >
            <GripVertical className="h-5 w-5" />
          </button>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-semibold text-foreground">{experience.role}</h3>
                <p className="text-sm text-muted-foreground">{experience.company}</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {formatDateRange()} • {experience.location}
                </p>
              </div>

              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onEdit(experience)}
                >
                  <Edit className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDelete(experience.id)}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsExpanded(!isExpanded)}
                >
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* Expanded Content */}
            {isExpanded && experience.summary && (
              <div className="mt-4 pt-4 border-t border-border">
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {experience.summary}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
