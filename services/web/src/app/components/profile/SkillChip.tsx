import React from 'react';
import { X } from 'lucide-react';

export type SkillProficiency = 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert';
export type SkillCategory = 'Technical' | 'Tools' | 'Soft Skills' | 'Domain';

interface SkillChipProps {
  name: string;
  proficiency?: SkillProficiency;
  category?: SkillCategory;
  onRemove?: () => void;
  onClick?: () => void;
  error?: boolean;
  selected?: boolean;
}

const proficiencyColors: Record<SkillProficiency, string> = {
  Beginner: 'bg-muted text-muted-foreground',
  Intermediate: 'bg-info/10 text-info',
  Advanced: 'bg-brand/10 text-brand',
  Expert: 'bg-success/10 text-success',
};

export const SkillChip: React.FC<SkillChipProps> = ({
  name,
  proficiency,
  category,
  onRemove,
  onClick,
  error = false,
  selected = false,
}) => {
  const baseClasses = 'inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-colors';

  let colorClasses = 'bg-secondary text-secondary-foreground';

  if (error) {
    colorClasses = 'bg-destructive/10 text-destructive border border-destructive/20';
  } else if (selected) {
    colorClasses = 'bg-brand text-brand-foreground';
  } else if (proficiency) {
    colorClasses = proficiencyColors[proficiency];
  }

  const isInteractive = onClick || onRemove;

  return (
    <div
      className={`${baseClasses} ${colorClasses} ${isInteractive ? 'cursor-pointer hover:opacity-80' : ''}`}
      onClick={onClick}
    >
      <span className="font-medium">{name}</span>
      {proficiency && (
        <span className="text-xs opacity-75">• {proficiency}</span>
      )}
      {category && !proficiency && (
        <span className="text-xs opacity-75">({category})</span>
      )}
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="p-0.5 hover:bg-black/10 rounded-full transition-colors"
          aria-label={`Remove ${name}`}
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </div>
  );
};
