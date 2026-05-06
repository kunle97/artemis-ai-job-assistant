'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '../components/AppShell';
import { Button, Card, Badge } from '../components/ui';
import { Search, SlidersHorizontal, MapPin, DollarSign, Briefcase, Heart, X, RefreshCw } from 'lucide-react';

const mockJobs = [
  {
    id: '1',
    title: 'Senior Product Manager',
    company: 'TechCorp Inc.',
    location: 'San Francisco, CA',
    workMode: 'Hybrid',
    salary: '$150k - $200k',
    posted: '2 days ago',
    description: 'Leading product strategy for our flagship SaaS platform...',
  },
  {
    id: '2',
    title: 'Product Manager',
    company: 'Innovate Labs',
    location: 'Remote',
    workMode: 'Remote',
    salary: '$130k - $170k',
    posted: '1 week ago',
    description: 'Drive product vision and roadmap for AI-powered tools...',
  },
  {
    id: '3',
    title: 'Product Lead',
    company: 'StartupXYZ',
    location: 'New York, NY',
    workMode: 'On-site',
    salary: '$140k - $180k',
    posted: '3 days ago',
    description: 'Own end-to-end product development lifecycle...',
  },
];

export const JobFeedDashboard: React.FC = () => {
  const router = useRouter();
  const [jobs, setJobs] = useState(mockJobs);
  const [scanning, setScanning] = useState(false);

  const handleScanJobs = () => {
    setScanning(true);
    setTimeout(() => {
      setScanning(false);
    }, 2000);
  };

  const handleSaveJob = (jobId: string) => {
    router.push(`/applications/new?jobId=${jobId}`);
  };

  const handleDismissJob = (jobId: string) => {
    setJobs(jobs.filter((j) => j.id !== jobId));
  };

  const handleGoToPreferences = () => {
    router.push('/preferences');
  };

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-semibold text-foreground">Job Feed</h1>
              <p className="mt-2 text-muted-foreground">Discover opportunities matched to your preferences</p>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" onClick={handleGoToPreferences}>
                <SlidersHorizontal className="h-4 w-4" />
                Preferences
              </Button>
              <Button variant="primary" onClick={handleScanJobs} loading={scanning}>
                <RefreshCw className="h-4 w-4" />
                Scan Jobs
              </Button>
            </div>
          </div>
        </div>

        {/* Filters */}
        <Card padding="sm" variant="outlined" className="mb-6">
          <div className="flex items-center gap-4">
            <div className="flex-1 flex items-center gap-2 px-3 py-2 rounded-lg bg-input-background border border-border">
              <Search className="h-5 w-5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search jobs..."
                className="flex-1 bg-transparent border-none outline-none text-foreground placeholder:text-muted-foreground"
              />
            </div>
            <select className="px-4 py-2 rounded-lg bg-input-background border border-border text-foreground">
              <option>All Locations</option>
              <option>Remote</option>
              <option>San Francisco</option>
              <option>New York</option>
            </select>
            <select className="px-4 py-2 rounded-lg bg-input-background border border-border text-foreground">
              <option>All Work Modes</option>
              <option>Remote</option>
              <option>Hybrid</option>
              <option>On-site</option>
            </select>
          </div>
        </Card>

        {/* Results Count */}
        <div className="mb-4">
          <p className="text-sm text-muted-foreground">{jobs.length} opportunities found</p>
        </div>

        {/* Job Cards */}
        <div className="space-y-4">
          {jobs.map((job) => (
            <Card key={job.id} padding="md" variant="outlined" className="hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between gap-6">
                <div className="flex-1">
                  <div className="flex items-start gap-4">
                    <div className="h-12 w-12 rounded-lg bg-brand/10 flex items-center justify-center flex-shrink-0">
                      <Briefcase className="h-6 w-6 text-brand" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold text-foreground mb-1">{job.title}</h3>
                      <p className="text-foreground mb-3">{job.company}</p>

                      <div className="flex flex-wrap items-center gap-3 mb-4">
                        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                          <MapPin className="h-4 w-4" />
                          {job.location}
                        </div>
                        <Badge variant="default" size="sm">
                          {job.workMode}
                        </Badge>
                        {job.salary && (
                          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                            <DollarSign className="h-4 w-4" />
                            {job.salary}
                          </div>
                        )}
                        <span className="text-sm text-muted-foreground">{job.posted}</span>
                      </div>

                      <p className="text-muted-foreground line-clamp-2">{job.description}</p>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-2">
                  <Button variant="primary" size="sm" onClick={() => handleSaveJob(job.id)}>
                    <Heart className="h-4 w-4" />
                    Apply
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleDismissJob(job.id)}>
                    <X className="h-4 w-4" />
                    Dismiss
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Empty State */}
        {jobs.length === 0 && (
          <Card padding="lg" className="text-center">
            <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">No more jobs in your feed</h3>
            <p className="text-muted-foreground mb-6">
              Try scanning for new opportunities or adjusting your preferences
            </p>
            <div className="flex items-center justify-center gap-3">
              <Button variant="outline" onClick={handleGoToPreferences}>
                Update Preferences
              </Button>
              <Button variant="primary" onClick={handleScanJobs}>
                Scan for Jobs
              </Button>
            </div>
          </Card>
        )}
      </div>
    </AppShell>
  );
};
