import React, { useState } from 'react';
import { SkillChip, SkillProficiency, SkillCategory } from './SkillChip';
import { Input, Button } from '../ui';
import { Plus, Search } from 'lucide-react';

export interface Skill {
  id: string;
  name: string;
  proficiency?: SkillProficiency;
  category?: SkillCategory;
}

interface SkillEditorProps {
  skills: Skill[];
  onChange: (skills: Skill[]) => void;
}

const SKILL_SUGGESTIONS = [
  'JavaScript', 'TypeScript', 'React', 'Node.js', 'Python', 'Java', 'SQL',
  'Communication', 'Leadership', 'Project Management', 'Problem Solving',
  'Data Analysis', 'UI/UX Design', 'Agile', 'Git', 'AWS', 'Docker'
];

const PROFICIENCY_OPTIONS: SkillProficiency[] = ['Beginner', 'Intermediate', 'Advanced', 'Expert'];
const CATEGORY_OPTIONS: SkillCategory[] = ['Technical', 'Tools', 'Soft Skills', 'Domain'];

export const SkillEditor: React.FC<SkillEditorProps> = ({ skills, onChange }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [newSkillName, setNewSkillName] = useState('');
  const [selectedProficiency, setSelectedProficiency] = useState<SkillProficiency>('Intermediate');
  const [selectedCategory, setSelectedCategory] = useState<SkillCategory>('Technical');
  const [error, setError] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  const filteredSuggestions = SKILL_SUGGESTIONS.filter(
    skill =>
      skill.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !skills.some(s => s.name.toLowerCase() === skill.toLowerCase())
  );

  const handleAddSkill = () => {
    if (!newSkillName.trim()) {
      setError('Skill name cannot be empty');
      return;
    }

    if (skills.some(s => s.name.toLowerCase() === newSkillName.trim().toLowerCase())) {
      setError('This skill already exists');
      return;
    }

    const newSkill: Skill = {
      id: Date.now().toString(),
      name: newSkillName.trim(),
      proficiency: selectedProficiency,
      category: selectedCategory,
    };

    onChange([...skills, newSkill]);
    setNewSkillName('');
    setError('');
    setShowAddForm(false);
  };

  const handleRemoveSkill = (id: string) => {
    onChange(skills.filter(s => s.id !== id));
  };

  const handleAddFromSuggestion = (skillName: string) => {
    const newSkill: Skill = {
      id: Date.now().toString(),
      name: skillName,
      proficiency: 'Intermediate',
      category: 'Technical',
    };
    onChange([...skills, newSkill]);
    setSearchTerm('');
  };

  return (
    <div className="space-y-4">
      {/* Search and Add Controls */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search skills..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <Button
          variant="outline"
          onClick={() => setShowAddForm(!showAddForm)}
        >
          <Plus className="h-4 w-4" />
          Add Skill
        </Button>
      </div>

      {/* Suggestions */}
      {searchTerm && filteredSuggestions.length > 0 && (
        <div className="p-3 border border-border rounded-lg bg-muted/30">
          <p className="text-sm text-muted-foreground mb-2">Suggestions:</p>
          <div className="flex flex-wrap gap-2">
            {filteredSuggestions.slice(0, 8).map(skill => (
              <button
                key={skill}
                onClick={() => handleAddFromSuggestion(skill)}
                className="px-3 py-1.5 rounded-full bg-background border border-border text-sm hover:bg-accent transition-colors"
              >
                {skill}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Add Skill Form */}
      {showAddForm && (
        <div className="p-4 border border-border rounded-lg bg-background space-y-3">
          <Input
            label="Skill Name"
            value={newSkillName}
            onChange={(e) => setNewSkillName(e.target.value)}
            error={error}
            placeholder="e.g., React, Leadership, SQL"
          />

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Proficiency
              </label>
              <select
                value={selectedProficiency}
                onChange={(e) => setSelectedProficiency(e.target.value as SkillProficiency)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {PROFICIENCY_OPTIONS.map(level => (
                  <option key={level} value={level}>{level}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Category
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value as SkillCategory)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {CATEGORY_OPTIONS.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex gap-2 justify-end">
            <Button variant="ghost" onClick={() => { setShowAddForm(false); setError(''); }}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleAddSkill}>
              Add Skill
            </Button>
          </div>
        </div>
      )}

      {/* Skills List */}
      {skills.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {skills.map(skill => (
            <SkillChip
              key={skill.id}
              name={skill.name}
              proficiency={skill.proficiency}
              category={skill.category}
              onRemove={() => handleRemoveSkill(skill.id)}
            />
          ))}
        </div>
      ) : (
        <div className="p-8 text-center border border-dashed border-border rounded-lg bg-muted/20">
          <p className="text-muted-foreground mb-2">No skills added yet</p>
          <p className="text-sm text-muted-foreground">
            Add skills to help Artemis match you with relevant opportunities and autofill applications.
          </p>
        </div>
      )}
    </div>
  );
};
