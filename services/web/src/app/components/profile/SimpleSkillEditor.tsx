import React, { useState } from 'react';
import { X, Plus } from 'lucide-react';
import { Button, Input } from '../ui';

export interface SimpleSkill {
  id: string;
  name: string;
}

interface SimpleSkillEditorProps {
  skills: SimpleSkill[];
  onChange: (skills: SimpleSkill[]) => void;
}

export const SimpleSkillEditor: React.FC<SimpleSkillEditorProps> = ({ skills, onChange }) => {
  const [newSkill, setNewSkill] = useState('');
  const [error, setError] = useState('');

  const handleAdd = () => {
    if (!newSkill.trim()) {
      setError('Skill name cannot be empty');
      return;
    }

    if (skills.some(s => s.name.toLowerCase() === newSkill.trim().toLowerCase())) {
      setError('This skill already exists');
      return;
    }

    onChange([...skills, { id: Date.now().toString(), name: newSkill.trim() }]);
    setNewSkill('');
    setError('');
  };

  const handleRemove = (id: string) => {
    onChange(skills.filter(s => s.id !== id));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAdd();
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input
          placeholder="Add a skill (e.g., React, Leadership, SQL)"
          value={newSkill}
          onChange={(e) => {
            setNewSkill(e.target.value);
            setError('');
          }}
          onKeyPress={handleKeyPress}
          error={error}
        />
        <Button variant="primary" onClick={handleAdd}>
          <Plus className="h-4 w-4" />
          Add
        </Button>
      </div>

      {skills.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {skills.map(skill => (
            <div
              key={skill.id}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary text-foreground border border-border"
            >
              <span>{skill.name}</span>
              <button
                onClick={() => handleRemove(skill.id)}
                className="p-0.5 hover:bg-destructive/10 rounded-full transition-colors"
                aria-label={`Remove ${skill.name}`}
              >
                <X className="h-4 w-4 text-muted-foreground hover:text-destructive" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-8 text-center border border-dashed border-border rounded-lg bg-muted/20">
          <p className="text-muted-foreground text-sm">No skills added yet. Add skills to help with job matching.</p>
        </div>
      )}
    </div>
  );
};
