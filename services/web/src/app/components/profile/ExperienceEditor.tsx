import React, { useState } from 'react';
import { ExperienceCard, Experience } from './ExperienceCard';
import { Button, Card, CardContent } from '../ui';
import { Plus, Briefcase, AlertCircle } from 'lucide-react';

interface ExperienceEditorProps {
  experiences: Experience[];
  onChange: (experiences: Experience[]) => void;
}

export const ExperienceEditor: React.FC<ExperienceEditorProps> = ({ experiences, onChange }) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const handleAddNew = () => {
    const newExperience: Experience = {
      id: Date.now().toString(),
      role: '',
      company: '',
      startDate: '',
      endDate: null,
      currentlyWorking: false,
      location: '',
      summary: '',
    };
    onChange([newExperience, ...experiences]);
    setEditingId(newExperience.id);
  };

  const handleSave = (updatedExperience: Experience) => {
    onChange(experiences.map(exp =>
      exp.id === updatedExperience.id ? updatedExperience : exp
    ));
    setEditingId(null);
    setHasUnsavedChanges(false);
  };

  const handleCancelEdit = (id: string) => {
    if (hasUnsavedChanges) {
      if (!confirm('You have unsaved changes. Are you sure you want to cancel?')) {
        return;
      }
    }

    // If it's a new experience (empty fields), remove it
    const experience = experiences.find(exp => exp.id === id);
    if (experience && !experience.role && !experience.company) {
      onChange(experiences.filter(exp => exp.id !== id));
    }

    setEditingId(null);
    setHasUnsavedChanges(false);
  };

  const handleDelete = (id: string) => {
    setShowDeleteConfirm(id);
  };

  const confirmDelete = () => {
    if (showDeleteConfirm) {
      onChange(experiences.filter(exp => exp.id !== showDeleteConfirm));
      setShowDeleteConfirm(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-foreground">Work Experience</h3>
          <p className="text-sm text-muted-foreground">
            Add your professional experience to improve job matching and autofill applications
          </p>
        </div>
        <Button variant="outline" onClick={handleAddNew}>
          <Plus className="h-4 w-4" />
          Add Experience
        </Button>
      </div>

      {experiences.length > 0 ? (
        <div className="space-y-3">
          {experiences.map(experience => (
            <ExperienceCard
              key={experience.id}
              experience={experience}
              isEditing={editingId === experience.id}
              onEdit={(exp) => setEditingId(exp.id)}
              onDelete={handleDelete}
              onSave={handleSave}
              onCancelEdit={() => handleCancelEdit(experience.id)}
              hasUnsavedChanges={hasUnsavedChanges}
            />
          ))}
        </div>
      ) : (
        <div className="p-12 text-center border border-dashed border-border rounded-lg bg-muted/20">
          <Briefcase className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
          <p className="text-muted-foreground mb-2">No work experience added yet</p>
          <p className="text-sm text-muted-foreground mb-4">
            Add your professional experience to showcase your career journey
          </p>
          <Button variant="primary" onClick={handleAddNew}>
            <Plus className="h-4 w-4" />
            Add Your First Experience
          </Button>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
          <Card className="max-w-md mx-4">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="h-10 w-10 rounded-full bg-destructive/10 flex items-center justify-center flex-shrink-0">
                  <AlertCircle className="h-5 w-5 text-destructive" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-foreground mb-2">Delete Experience?</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Are you sure you want to delete this experience? This action cannot be undone.
                  </p>
                  <div className="flex gap-2 justify-end">
                    <Button variant="ghost" onClick={() => setShowDeleteConfirm(null)}>
                      Cancel
                    </Button>
                    <Button variant="danger" onClick={confirmDelete}>
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
