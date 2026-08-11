'use client';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { getStoredAccessToken } from '../../services/auth/auth.service';
import { AppShell } from '../components/AppShell';
import { Button, Card, Badge } from '../components/ui';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { Plus, CheckCircle, Clock, XCircle, ArrowRight, AlertCircle, Trash2 } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { ScoreIndicator } from '../components/ui/ScoreIndicator';
import type { ScoreRecommendation } from '../components/ui/ScoreIndicator';
import {
  listApplications,
  deleteApplication,
  getApplicationStatus,
  getJobById,
  type ApplicationRecord,
  type ApplicationStatusRecord,
} from '../../services/applications/application-workspace.service';
import {
  deriveApplicationStatusPresentation,
  type ApplicationStatusCategory,
} from '../../services/applications/application-status';

type ApplicationStatus = ApplicationStatusCategory;

interface ApplicationDisplay {
  id: string;
  jobId: string;
  jobTitle: string;
  company: string;
  rawStatus: string;
  status: ApplicationStatus;
  statusLabel: string;
  statusVariant: string;
  lastUpdated: string;
  fitScore?: number | null;
  fitRecommendation?: ScoreRecommendation;
}

const statusConfig: Record<ApplicationStatus, { label: string; variant: string; icon: LucideIcon }> = {
  draft: { label: 'Draft', variant: 'default', icon: Clock },
  ready: { label: 'Ready to Submit', variant: 'ready', icon: CheckCircle },
  blocked: { label: 'Blocked', variant: 'blocked', icon: XCircle },
  submitted: { label: 'Submitted', variant: 'success', icon: CheckCircle },
  'in-progress': { label: 'In Progress', variant: 'in-progress', icon: Clock },
};

function mapApplicationStatus(apiStatus: string): ApplicationStatus {
  return deriveApplicationStatusPresentation({ status: apiStatus }).category;
}

function deriveApplicationStatus(status: ApplicationStatusRecord): ApplicationStatus {
  return deriveApplicationStatusPresentation(status).category;
}

export const ApplicationsDashboard: React.FC = () => {
  const router = useRouter();
  const [filter, setFilter] = useState<ApplicationStatus | 'all'>('all');
  const [applications, setApplications] = useState<ApplicationDisplay[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingApplicationId, setDeletingApplicationId] = useState<string | null>(null);
  const [pendingDeleteApplication, setPendingDeleteApplication] = useState<ApplicationDisplay | null>(null);

  const postSubmissionStatuses = new Set([
    'submitted',
    'applied',
    'interviewing',
    'offer_received',
    'offer_accepted',
    'rejected',
    'archived',
  ]);

  const isUnsubmittedStatus = (status: string) => !postSubmissionStatuses.has((status || '').trim().toLowerCase());

  const buildDisplayApps = async (token: string, appRecords: ApplicationRecord[]): Promise<ApplicationDisplay[]> => {
    const displayApps: ApplicationDisplay[] = [];

    for (const app of appRecords) {
      try {
        const [statusRecord, job] = await Promise.all([
          getApplicationStatus(token, app.id),
          getJobById(token, app.job_id),
        ]);
        const statusPresentation = deriveApplicationStatusPresentation(statusRecord);
        displayApps.push({
          id: app.id,
          jobId: app.job_id,
          jobTitle: job?.title || `Job ${app.job_id.slice(0, 8)}`,
          company: job?.company_name || 'Unknown company',
          rawStatus: statusRecord.status,
          status: deriveApplicationStatus(statusRecord),
          statusLabel: statusPresentation.label,
          statusVariant: statusPresentation.variant,
          lastUpdated: new Date(app.updated_at).toLocaleDateString(),
          fitScore: job?.fit_score ?? null,
          fitRecommendation: job?.fit_recommendation ?? null,
        });
      } catch (statusErr) {
        console.warn(`Failed to load status for application ${app.id}:`, statusErr);
        const statusPresentation = deriveApplicationStatusPresentation(app);
        displayApps.push({
          id: app.id,
          jobId: app.job_id,
          jobTitle: `Job ${app.job_id.slice(0, 8)}`,
          company: 'Unknown company',
          rawStatus: app.status,
          status: mapApplicationStatus(app.status),
          statusLabel: statusPresentation.label,
          statusVariant: statusPresentation.variant,
          lastUpdated: new Date(app.updated_at).toLocaleDateString(),
          fitScore: null,
          fitRecommendation: null,
        });
      }
    }

    return displayApps;
  };

  useEffect(() => {
    const loadApplications = async () => {
      const token = getStoredAccessToken();
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        const appRecords = await listApplications(token);
        const displayApps = await buildDisplayApps(token, appRecords);

        setApplications(displayApps);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load applications';
        setError(message);
        setApplications([]);
      } finally {
        setIsLoading(false);
      }
    };

    loadApplications();
  }, []);

  const filteredApplications = applications.filter(
    (app) => filter === 'all' || app.status === filter
  );

  const statusCounts = {
    all: applications.length,
    ready: applications.filter((a) => a.status === 'ready').length,
    blocked: applications.filter((a) => a.status === 'blocked').length,
    'in-progress': applications.filter((a) => a.status === 'in-progress').length,
    submitted: applications.filter((a) => a.status === 'submitted').length,
    draft: applications.filter((a) => a.status === 'draft').length,
  };

  const handleViewApplication = (id: string) => {
    router.push(`/applications/${id}`);
  };

  const handleCreateApplication = () => {
    router.push('/jobs');
  };

  const handleDeleteApplication = async (app: ApplicationDisplay) => {
    if (!isUnsubmittedStatus(app.rawStatus)) {
      return;
    }

    setPendingDeleteApplication(app);
  };

  const confirmDeleteApplication = async () => {
    const app = pendingDeleteApplication;
    const token = getStoredAccessToken();
    if (!token || deletingApplicationId || !app) return;

    setDeletingApplicationId(app.id);
    try {
      await deleteApplication(token, app.id, true);
      setPendingDeleteApplication(null);
      const appRecords = await listApplications(token);
      const refreshed = await buildDisplayApps(token, appRecords);
      setApplications(refreshed);
      toast.success('Application deleted', {
        description: 'The job has been restored to your feed for retesting.',
      });
    } catch (deleteError) {
      const message = deleteError instanceof Error ? deleteError.message : 'Failed to delete application.';
      toast.error('Delete failed', { description: message });
    } finally {
      setDeletingApplicationId(null);
    }
  };

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-semibold text-foreground">Applications</h1>
              <p className="mt-2 text-muted-foreground">Track and manage all your job applications</p>
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => router.push('/applications/patterns')}>
                View Patterns
              </Button>
              <Button variant="primary" onClick={handleCreateApplication}>
                <Plus className="h-4 w-4" />
                New Application
              </Button>
            </div>
          </div>
        </div>

        {/* Status Overview */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
          {[
            { key: 'all', label: 'All', count: statusCounts.all, color: 'bg-muted' },
            { key: 'ready', label: 'Ready', count: statusCounts.ready, color: 'bg-ready' },
            { key: 'blocked', label: 'Blocked', count: statusCounts.blocked, color: 'bg-blocked' },
            { key: 'in-progress', label: 'In Progress', count: statusCounts['in-progress'], color: 'bg-in-progress' },
            { key: 'submitted', label: 'Submitted', count: statusCounts.submitted, color: 'bg-success' },
            { key: 'draft', label: 'Draft', count: statusCounts.draft, color: 'bg-muted' },
          ].map((item) => (
            <button
              key={item.key}
              onClick={() => setFilter(item.key as ApplicationStatus | 'all')}
              className={`text-left p-4 rounded-lg border-2 transition-all ${
                filter === item.key
                  ? 'border-brand bg-brand/5'
                  : 'border-border hover:border-brand/50 bg-card'
              }`}
            >
              <div className={`inline-block px-2 py-1 rounded text-white text-xs font-medium mb-2 ${item.color}`}>
                {item.count}
              </div>
              <p className="text-sm font-medium text-foreground">{item.label}</p>
            </button>
          ))}
        </div>

        {/* Applications Table */}
        <Card padding="none" variant="outlined">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-border bg-secondary/50">
                <tr>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Position</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Company</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Status</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Fit Score</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Last Updated</th>
                  <th className="text-right px-6 py-4 text-sm font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredApplications.map((app) => {
                  return (
                    <tr key={app.id} className="hover:bg-secondary/30 transition-colors">
                      <td className="px-6 py-4">
                        <p className="font-medium text-foreground">{app.jobTitle}</p>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-foreground">{app.company}</p>
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant={app.statusVariant} size="sm">
                          {app.statusLabel}
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        <ScoreIndicator
                          score={app.fitScore}
                          recommendation={app.fitRecommendation}
                          compact
                        />
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-muted-foreground">{app.lastUpdated}</span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="inline-flex items-center gap-1">
                          {isUnsubmittedStatus(app.rawStatus) ? (
                            <Button
                              variant="ghost"
                              size="icon"
                              disabled={deletingApplicationId === app.id}
                              onClick={() => void handleDeleteApplication(app)}
                              aria-label="Delete unsubmitted application"
                              title="Delete unsubmitted application"
                            >
                              <Trash2 className="h-4 w-4 text-muted-foreground" />
                            </Button>
                          ) : null}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewApplication(app.id)}
                          >
                            View
                            <ArrowRight className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {isLoading && (
            <div className="text-center py-12">
              <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4 animate-spin" />
              <h3 className="text-lg font-semibold text-foreground mb-2">Loading applications...</h3>
            </div>
          )}

          {error && !isLoading && (
            <div className="text-center py-12">
              <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">Error loading applications</h3>
              <p className="text-muted-foreground mb-6">{error}</p>
              <Button variant="primary" onClick={() => window.location.reload()}>
                Retry
              </Button>
            </div>
          )}

          {!isLoading && !error && filteredApplications.length === 0 && (
            <div className="text-center py-12">
              <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">No applications found</h3>
              <p className="text-muted-foreground mb-6">
                {filter === 'all'
                  ? 'Start by creating your first application'
                  : `No applications with status "${statusConfig[filter as ApplicationStatus]?.label}"`}
              </p>
              <Button variant="primary" onClick={handleCreateApplication}>
                <Plus className="h-4 w-4" />
                Create Application
              </Button>
            </div>
          )}
        </Card>

        <AlertDialog
          open={Boolean(pendingDeleteApplication)}
          onOpenChange={(open) => {
            if (!open && !deletingApplicationId) {
              setPendingDeleteApplication(null);
            }
          }}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete This Application?</AlertDialogTitle>
              <AlertDialogDescription>
                This will delete the unsubmitted application and move the job back into your feed so you can retest.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={Boolean(deletingApplicationId)}>Cancel</AlertDialogCancel>
              <AlertDialogAction
                className="bg-destructive text-white hover:bg-destructive/90"
                onClick={(event) => {
                  event.preventDefault();
                  void confirmDeleteApplication();
                }}
              >
                {deletingApplicationId ? 'Deleting...' : 'Delete Application'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </AppShell>
  );
};
