'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '../components/AppShell';
import { Button, Card, Badge } from '../components/ui';
import { Plus, AlertCircle, CheckCircle, Clock, XCircle, ArrowRight } from 'lucide-react';
import { ScoreIndicator } from '../components/ui/ScoreIndicator';
import type { ScoreRecommendation } from '../components/ui/ScoreIndicator';


type ApplicationStatus = 'draft' | 'ready' | 'blocked' | 'submitted' | 'in-progress';
type ReadinessStatus = 'complete' | 'partial' | 'blocked' | 'not-started';

interface Application {
  id: string;
  jobTitle: string;
  company: string;
  status: ApplicationStatus;
  readiness: ReadinessStatus;
  lastUpdated: string;
  blockers?: number;
  /** TODO: populated from POST /applications/{id}/score */
  fitScore?: number | null;
  fitRecommendation?: ScoreRecommendation;
}

const mockApplications: Application[] = [
  {
    id: '1',
    jobTitle: 'Senior Product Manager',
    company: 'TechCorp Inc.',
    status: 'ready',
    readiness: 'complete',
    lastUpdated: '2 hours ago',
    fitScore: 4.6,
    fitRecommendation: 'apply_immediately',
  },
  {
    id: '2',
    jobTitle: 'Product Manager',
    company: 'Innovate Labs',
    status: 'blocked',
    readiness: 'blocked',
    lastUpdated: '1 day ago',
    blockers: 3,
    fitScore: 3.2,
    fitRecommendation: 'recommend_against',
  },
  {
    id: '3',
    jobTitle: 'Product Lead',
    company: 'StartupXYZ',
    status: 'in-progress',
    readiness: 'partial',
    lastUpdated: '3 hours ago',
    fitScore: 4.1,
    fitRecommendation: 'worth_applying',
  },
  {
    id: '4',
    jobTitle: 'VP of Product',
    company: 'BigTech Co.',
    status: 'submitted',
    readiness: 'complete',
    lastUpdated: '2 days ago',
    fitScore: 3.7,
    fitRecommendation: 'apply_if_specific_reason',
  },
  {
    id: '5',
    jobTitle: 'Director of Product',
    company: 'Growth Startup',
    status: 'draft',
    readiness: 'not-started',
    lastUpdated: '1 week ago',
    fitScore: null,
    fitRecommendation: null,
  },
];

const statusConfig: Record<ApplicationStatus, { label: string; variant: any; icon: any }> = {
  draft: { label: 'Draft', variant: 'default', icon: Clock },
  ready: { label: 'Ready to Submit', variant: 'ready', icon: CheckCircle },
  blocked: { label: 'Blocked', variant: 'blocked', icon: XCircle },
  submitted: { label: 'Submitted', variant: 'success', icon: CheckCircle },
  'in-progress': { label: 'In Progress', variant: 'in-progress', icon: Clock },
};

export const ApplicationsDashboard: React.FC = () => {
  const router = useRouter();
  const [filter, setFilter] = useState<ApplicationStatus | 'all'>('all');
  const applications = mockApplications.filter((app) => filter === 'all' || app.status === filter);

  const statusCounts = {
    all: mockApplications.length,
    ready: mockApplications.filter((a) => a.status === 'ready').length,
    blocked: mockApplications.filter((a) => a.status === 'blocked').length,
    'in-progress': mockApplications.filter((a) => a.status === 'in-progress').length,
    submitted: mockApplications.filter((a) => a.status === 'submitted').length,
    draft: mockApplications.filter((a) => a.status === 'draft').length,
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
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Readiness</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Fit Score</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Last Updated</th>
                  <th className="text-right px-6 py-4 text-sm font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {applications.map((app) => {
                  const StatusIcon = statusConfig[app.status].icon;
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
                        <div className="flex items-center gap-2">
                          {app.readiness === 'complete' && (
                            <CheckCircle className="h-4 w-4 text-success" />
                          )}
                          {app.readiness === 'blocked' && (
                            <>
                              <AlertCircle className="h-4 w-4 text-destructive" />
                              <span className="text-sm text-muted-foreground">{app.blockers} blockers</span>
                            </>
                          )}
                          {app.readiness === 'partial' && (
                            <Clock className="h-4 w-4 text-warning" />
                          )}
                          {app.readiness === 'not-started' && (
                            <span className="text-sm text-muted-foreground">Not started</span>
                          )}
                        </div>
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

          {applications.length === 0 && (
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
