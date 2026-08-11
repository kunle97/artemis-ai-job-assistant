/**
 * Shared application status presentation rules used by list and detail views.
 */

export type ApplicationStatusCategory = 'draft' | 'ready' | 'blocked' | 'submitted' | 'in-progress';

export interface ApplicationStatusPresentationInput {
  status: string;
  manual_review_required?: boolean;
  missing_items?: string[];
  failure_reason?: string | null;
}

export interface ApplicationStatusPresentation {
  category: ApplicationStatusCategory;
  label: string;
  variant: string;
}

function normalize(status: string): string {
  return (status || '').trim().toLowerCase();
}

function formatLabel(status: string): string {
  return status.replace(/[-_]+/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase());
}

export function deriveApplicationStatusPresentation(
  input: ApplicationStatusPresentationInput,
): ApplicationStatusPresentation {
  const status = normalize(input.status);

  if (['submitted', 'applied'].includes(status)) {
    return { category: 'submitted', label: 'Submitted', variant: 'success' };
  }
  if (['queued', 'running', 'in_progress', 'in-progress', 'inspecting', 'inspected', 'planning', 'planned', 'filling'].includes(status)) {
    return { category: 'in-progress', label: formatLabel(status), variant: 'in-progress' };
  }
  if (status === 'failed' || input.failure_reason) {
    return { category: 'blocked', label: 'Failed', variant: 'blocked' };
  }
  if (['rejected', 'archived', 'needs_review'].includes(status)) {
    return {
      category: 'blocked',
      label: status === 'needs_review' ? 'Needs Review' : formatLabel(status),
      variant: status === 'needs_review' ? 'warning' : 'blocked',
    };
  }
  if ((input.missing_items?.length ?? 0) > 0) {
    return { category: 'blocked', label: 'Blocked', variant: 'blocked' };
  }
  if (input.manual_review_required) {
    return { category: 'blocked', label: 'Needs Review', variant: 'warning' };
  }
  if (['filled', 'authorized', 'awaiting_submission', 'ready_to_submit', 'ready', 'offer_received', 'interviewing'].includes(status)) {
    return { category: 'ready', label: formatLabel(status), variant: 'ready' };
  }

  return { category: 'draft', label: formatLabel(status || 'draft'), variant: 'default' };
}
