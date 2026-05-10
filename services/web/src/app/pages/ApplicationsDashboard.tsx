'use client';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getStoredAccessToken } from '../../services/auth/auth.service';
import { AppShell } from '../components/AppShell';
import { Button, Card, Badge } from '../components/ui';
import { Plus, CheckCircle, Clock, XCircle, ArrowRight, AlertCircle } from 'lucide-react';
import { ScoreIndicator } from '../components/ui/ScoreIndicator';
import type { ScoreRecommendation } from '../components/ui/ScoreIndicator';
import {
  listApplications,
  getApplicationStatus,
  getJobById,
  type ApplicationStatusRecord,
} from '../../services/applications/application-workspace.service';

type ApplicationStatus = 'draft' | 'ready' | 'blocked' | 'submitted' | 'in-progress';

interface ApplicationDisplay {
  id: string;
  jobTitle: string;
  company: string;
  status: ApplicationStatus;
  lastUpdated: string;
  fitScore?: number | null;
  fitRecommendation?: ScoreRecommendation;
}

const statusConfig: Record<ApplicationStatus, { label: string; variant: any; icon: any }> = {
  draft: { label: 'Draft', variant: 'default', icon: Clock },
  ready: { label: 'Ready to Submit', variant: 'ready', icon: CheckCircle },
  blocked: { label: 'Blocked', variant: 'blocked', icon: XCircle },
  submitted: { label: 'Submitted', variant: 'success', icon: CheckCircle },
  'in-progress': { label: 'In Progress', variant: 'in-progress', icon: Clock },
};

function mapApplicationStatus(apiStatus: string): ApplicationStatus {
  const normalized = apiStatus.trim().toLowerCase();

  if (['submitted', 'applied'].includes(normalized)) return 'submitted';
  if (['failed', 'rejected', 'archived', 'needs_review'].includes(normalized)) return 'blocked';
  if (['filled', 'awaiting_submission', 'ready', 'offer_received', 'interviewing'].includes(normalized)) return 'ready';
  if (['queued', 'inspecting', 'inspected', 'planning', 'planned', 'filling', 'in_progress', 'in-progress'].includes(normalized)) {
    return 'in-progress';
  }
  if (['saved', 'draft'].includes(normalized)) return 'draft';

  return 'draft';
}

function deriveApplicationStatus(status: ApplicationStatusRecord): ApplicationStatus {
  const normalized = status.status.trim().toLowerCase();
  if (['submitted', 'applied'].includes(normalized)) return 'submitted';
  if (['queued', 'inspecting', 'inspected', 'planning', 'planned', 'filling', 'in_progress', 'in-progress'].includes(normalized)) {
    return 'in-progress';
  }
  if (status.manual_review_required || status.missing_items.length > 0) return 'blocked';
  return mapApplicationStatus(status.status);
}

export const ApplicationsDashboard: React.FC = () => {
  const router = useRouter();
  const [filter, setFilter] = useState<ApplicationStatus | 'all'>('all');
  const [applications, setApplications] = useState<ApplicationDisplay[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
        const displayApps: ApplicationDisplay[] = [];

        for (const app of appRecords) {
          try {
            const [statusRecord, job] = await Promise.all([
              getApplicationStatus(token, app.id),
              getJobById(token, app.job_id),
            ]);
            displayApps.push({
              id: app.id,
              jobTitle: job?.title || `Job ${app.job_id.slice(0, 8)}`,
              company: job?.company_name || 'Unknown company',
              status: deriveApplicationStatus(statusRecord),
              lastUpdated: new Date(app.updated_at).toLocaleDateString(),
              fitScore: job?.fit_score ?? null,
              fitRecommendation: job?.fit_recommendation ?? null,
            });
          } catch (statusErr) {
            console.warn(`Failed to load status for application ${app.id}:`, statusErr);
            displayApps.push({
              id: app.id,
              jobTitle: `Job ${app.job_id.slice(0, 8)}`,
              company: 'Unknown company',
              status: mapApplicationStatus(app.status),
              lastUpdated: new Date(app.updated_at).toLocaleDateString(),
              fitScore: null,
              fitRecommendation: null,
            });
          }
        }

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
            <Button variant="primary" onClick={handleCreateApplication}>
              <Plus className="h-4 w-4" />
              New Application
            </Button>
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
              onClick={() => setFilter(item.key as any)}
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
                        <Badge variant={statusConfig[app.status].variant} size="sm">
                          {statusConfig[app.status].label}
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
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewApplication(app.id)}
                        >
                          View
                          <ArrowRight className="h-4 w-4" />
                        </Button>
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
      </div>
    </AppShell>
  );
};
