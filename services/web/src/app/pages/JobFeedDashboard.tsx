'use client';
import React, { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '../components/AppShell';
import { Button, Card, Badge, Input, ScoreIndicator } from '../components/ui';
import {
  Search,
  SlidersHorizontal,
  MapPin,
  DollarSign,
  Briefcase,
  Heart,
  X,
  RefreshCw,
  Loader2,
  Link,
  Plus,
  Zap,
} from 'lucide-react';
import {
  getJobFeed,
  scanJobFeed,
  updateFeedJobStatus,
  type FeedPageResponse,
  type JobFeedSortOrder,
  type JobItem,
} from '../../services/jobs/job-feed.service';
import {
  createApplication,
  runApplicationPipeline,
} from '../../services/applications/application-workspace.service';
import { getStoredAccessToken } from '../../services/auth/auth.service';

export const JobFeedDashboard: React.FC = () => {
  const router = useRouter();
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [hasScanned, setHasScanned] = useState(false);
  const [scanMessage, setScanMessage] = useState<string | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);
  const [statusTransitionError, setStatusTransitionError] = useState<string | null>(null);
  const [loadingFeed, setLoadingFeed] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [jobUpdatingId, setJobUpdatingId] = useState<string | null>(null);
  const [skip, setSkip] = useState(0);
  const [itemsPerPage, setItemsPerPage] = useState(12);
  const [total, setTotal] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);

  const [keywordFilter, setKeywordFilter] = useState('');
  const [locationFilter, setLocationFilter] = useState('All Locations');
  const [workModeFilter, setWorkModeFilter] = useState('All Work Modes');
  const [platformFilter, setPlatformFilter] = useState<Set<string>>(new Set());
  const [sortOrder, setSortOrder] = useState<JobFeedSortOrder>('newest');
  const [isKeywordSearchActive, setIsKeywordSearchActive] = useState(false);

  const [jobStatuses, setJobStatuses] = useState<Record<string, 'saved' | 'dismissed'>>({});
  const [applyingJobId, setApplyingJobId] = useState<string | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);

  const token = getStoredAccessToken();

  const hydratePageState = (page: FeedPageResponse, pageSkip: number) => {
    setJobs(page.jobs);
    setTotal(page.total);
    setHasNext(page.has_next);
    setHasPrev(pageSkip > 0);
    setSkip(pageSkip);
  };

  const loadFeed = async (pageSkip = 0, query?: string, sort: JobFeedSortOrder = sortOrder) => {
    if (!token) {
      setLoadingFeed(false);
      setScanError('Please sign in to view your job feed.');
      return;
    }

    setLoadingFeed(true);
    setScanError(null);

    try {
      const activeSources = platformFilter.size > 0 ? Array.from(platformFilter) : undefined;
      const page = await getJobFeed(token, pageSkip, itemsPerPage, query, sort, activeSources);
      hydratePageState(page, pageSkip);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load job feed.';
      setScanError(message);
    } finally {
      setLoadingFeed(false);
    }
  };

  useEffect(() => {
    const activeQuery = keywordFilter.trim() ? keywordFilter.trim() : undefined;
    void loadFeed(0, activeQuery, sortOrder);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [itemsPerPage, sortOrder, platformFilter]);

  // Debounced keyword search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (keywordFilter.trim() && !token) {
        setScanError('Please sign in to search jobs.');
        return;
      }

      if (keywordFilter.trim()) {
        void handleKeywordSearch();
      } else if (!keywordFilter.trim() && isKeywordSearchActive) {
        // If user clears the keyword filter, go back to regular feed
        setIsKeywordSearchActive(false);
        void loadFeed(0, undefined, sortOrder);
      }
    }, 500);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [keywordFilter]);

  const handleScanJobs = async () => {
    if (!token) {
      setScanError('Please sign in to scan for jobs.');
      return;
    }

    setScanning(true);
    setScanError(null);

    try {
      const response = await scanJobFeed(token);
      setHasScanned(true);
      setScanMessage(
        response.new_jobs_found > 0
          ? `Scan complete. ${response.new_jobs_found} new job${response.new_jobs_found === 1 ? '' : 's'} found.`
          : 'Scan complete. No new jobs found.',
      );
      await loadFeed(0, undefined, sortOrder);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Job scan failed.';
      setScanError(message);
    } finally {
      setScanning(false);
    }
  };

  const handleSaveJob = async (jobId: string) => {
    if (!token) {
      setStatusTransitionError('Please sign in to save jobs.');
      return;
    }

    setJobUpdatingId(jobId);
    setStatusTransitionError(null);

    try {
      await updateFeedJobStatus(token, jobId, 'saved');
      setJobStatuses((prev) => ({ ...prev, [jobId]: 'saved' }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to save job.';
      setStatusTransitionError(message);
    } finally {
      setJobUpdatingId(null);
    }
  };

  const handleDismissJob = async (jobId: string) => {
    if (!token) {
      setStatusTransitionError('Please sign in to dismiss jobs.');
      return;
    }

    setJobUpdatingId(jobId);
    setStatusTransitionError(null);

    try {
      await updateFeedJobStatus(token, jobId, 'dismissed');
      setJobStatuses((prev) => ({ ...prev, [jobId]: 'dismissed' }));
      setJobs((prev) => prev.filter((j) => j.id !== jobId));
      setTotal((prev) => Math.max(0, prev - 1));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to dismiss job.';
      setStatusTransitionError(message);
    } finally {
      setJobUpdatingId(null);
    }
  };

  const handleAutoApply = async (jobId: string) => {
    if (!token) {
      setApplyError('Please sign in to apply.');
      return;
    }

    setApplyingJobId(jobId);
    setApplyError(null);

    try {
      const application = await createApplication(token, { job_id: jobId });
      await runApplicationPipeline(token, application.id);
      router.push(`/applications/${application.id}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to start application.';
      setApplyError(message);
      setApplyingJobId(null);
    }
  };

  const handleKeywordSearch = async () => {
    if (!token) {
      return;
    }

    setLoadingFeed(true);
    setScanError(null);

    try {
      setIsKeywordSearchActive(true);
      const activeSources = platformFilter.size > 0 ? Array.from(platformFilter) : undefined;
      const page = await getJobFeed(token, 0, itemsPerPage, keywordFilter.trim(), sortOrder, activeSources);
      hydratePageState(page, 0);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Search failed.';
      setScanError(message);
    } finally {
      setLoadingFeed(false);
    }
  };

  const handlePageChange = async (direction: 'next' | 'prev') => {
    if (!token) {
      return;
    }

    const nextSkip = direction === 'next' ? skip + itemsPerPage : Math.max(0, skip - itemsPerPage);

    if (isKeywordSearchActive) {
      setLoadingFeed(true);
      try {
        const activeSources = platformFilter.size > 0 ? Array.from(platformFilter) : undefined;
        const page = await getJobFeed(token, nextSkip, itemsPerPage, keywordFilter.trim(), sortOrder, activeSources);
        hydratePageState(page, nextSkip);
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Pagination failed.';
        setScanError(message);
      } finally {
        setLoadingFeed(false);
      }
    } else {
      await loadFeed(nextSkip, undefined, sortOrder);
    }
  };

  const togglePlatform = (platform: string) => {
    setPlatformFilter((prev) => {
      const next = new Set(prev);
      if (next.has(platform)) {
        next.delete(platform);
      } else {
        next.add(platform);
      }
      return next;
    });
  };

  const visibleJobs = useMemo(() => {
    let filtered = [...jobs];

    if (locationFilter !== 'All Locations') {
      filtered = filtered.filter((job) => (job.location || 'Unknown').includes(locationFilter));
    }

    if (workModeFilter !== 'All Work Modes') {
      filtered = filtered.filter((job) => (job.workplace_type || 'Unknown') === workModeFilter);
    }

    return filtered;
  }, [jobs, locationFilter, workModeFilter]);

  const formatSalary = (job: JobItem): string | null => {
    if (job.salary_min == null && job.salary_max == null) return null;
    const prefix = job.currency ? `${job.currency} ` : '$';
    if (job.salary_min != null && job.salary_max != null) {
      return `${prefix}${job.salary_min.toLocaleString()} - ${prefix}${job.salary_max.toLocaleString()}`;
    }
    return `${prefix}${(job.salary_min || job.salary_max || 0).toLocaleString()}`;
  };

  const handleGoToPreferences = () => {
    router.push('/account');
  };

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-semibold text-foreground">Job Feed</h1>
              <p className="mt-2 text-muted-foreground">Scan, review, and organize opportunities into saved and dismissed buckets</p>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" onClick={() => router.push('/jobs/add')}>
                <Plus className="h-4 w-4" />
                Add Job by URL
              </Button>
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
          {scanMessage && <p className="mt-2 text-sm text-brand">{scanMessage}</p>}
          {scanError && <p className="mt-2 text-sm text-destructive">{scanError}</p>}
          {statusTransitionError && <p className="mt-2 text-sm text-destructive">{statusTransitionError}</p>}
          {applyError && <p className="mt-2 text-sm text-destructive">{applyError}</p>}
        </div>

        {/* Filters */}
        <Card padding="sm" variant="outlined" className="mb-6">
          <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
            <div className="flex-1 flex items-center gap-2 px-3 py-2 rounded-lg bg-input-background border border-border">
              <Search className="h-5 w-5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search jobs..."
                value={keywordFilter}
                onChange={(e) => setKeywordFilter(e.target.value)}
                className="flex-1 bg-transparent border-none outline-none text-foreground placeholder:text-muted-foreground"
              />
            </div>
            <select
              className="px-4 py-2 rounded-lg bg-input-background border border-border text-foreground"
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
            >
              <option>All Locations</option>
              <option>Remote</option>
              <option>San Francisco</option>
              <option>New York</option>
            </select>
            <select
              className="px-4 py-2 rounded-lg bg-input-background border border-border text-foreground"
              value={workModeFilter}
              onChange={(e) => setWorkModeFilter(e.target.value)}
            >
              <option>All Work Modes</option>
              <option>Remote</option>
              <option>Hybrid</option>
              <option>On-site</option>
            </select>
            <select
              className="px-4 py-2 rounded-lg bg-input-background border border-border text-foreground"
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value as JobFeedSortOrder)}
            >
              <option value="newest">Sort: Newest</option>
              <option value="fit_high">Sort: Fit Score</option>
              <option value="salary_high">Sort: Salary High</option>
              <option value="salary_low">Sort: Salary Low</option>
            </select>
            <select
              className="px-4 py-2 rounded-lg bg-input-background border border-border text-foreground"
              value={itemsPerPage}
              onChange={(e) => setItemsPerPage(Number(e.target.value))}
            >
              <option value={10}>10 per page</option>
              <option value={12}>12 per page</option>
              <option value={20}>20 per page</option>
              <option value={50}>50 per page</option>
            </select>
          </div>
          {/* Platform filter */}
          <div className="flex items-center gap-6 pt-2 border-t border-border">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Platform</span>
            {(['greenhouse', 'lever', 'ashby'] as const).map((platform) => (
              <label key={platform} className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={platformFilter.has(platform)}
                  onChange={() => togglePlatform(platform)}
                  className="h-4 w-4 rounded border-border accent-brand cursor-pointer"
                />
                <span className="text-sm text-foreground capitalize">{platform}</span>
              </label>
            ))}
            {platformFilter.size > 0 && (
              <button
                onClick={() => setPlatformFilter(new Set())}
                className="ml-auto text-xs text-muted-foreground hover:text-foreground"
              >
                Clear
              </button>
            )}
          </div>
          </div>
        </Card>

        {/* Results Count */}
        <div className="mb-4">
          <p className="text-sm text-muted-foreground">
            {visibleJobs.length} shown of {total} total opportunities
          </p>
        </div>

        {loadingFeed && (
          <Card padding="lg" className="text-center mb-6">
            <Loader2 className="h-8 w-8 text-brand animate-spin mx-auto mb-3" />
            <p className="text-muted-foreground">Loading job feed...</p>
          </Card>
        )}

        {/* Job Cards */}
        {!loadingFeed && visibleJobs.length > 0 && (
        <div className="space-y-4">
          {visibleJobs.map((job) => (
            <Card key={job.id} padding="md" variant="outlined" className="hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between gap-6">
                <div className="flex-1">
                  <div className="flex items-start gap-4">
                    <div className="h-12 w-12 rounded-lg bg-brand/10 flex items-center justify-center flex-shrink-0">
                      <Briefcase className="h-6 w-6 text-brand" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold text-foreground mb-1">{job.title}</h3>
                      <div className="mb-3 flex flex-wrap items-center gap-3">
                        <p className="text-foreground">{job.company_name}</p>
                        <span className="h-4 w-px bg-border" aria-hidden="true" />
                        <ScoreIndicator
                          compact
                          score={job.fit_score}
                          recommendation={job.fit_recommendation}
                          lowConfidence={job.fit_score_confidence === 'low'}
                        />
                      </div>

                      <div className="flex flex-wrap items-center gap-3 mb-4">
                        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                          <MapPin className="h-4 w-4" />
                          {job.location || 'Location not provided'}
                        </div>
                        {job.workplace_type && (
                          <Badge variant="default" size="sm">
                            {job.workplace_type}
                          </Badge>
                        )}
                        {formatSalary(job) && (
                          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                            <DollarSign className="h-4 w-4" />
                            {formatSalary(job)}
                          </div>
                        )}
                        <Badge variant="secondary" size="sm">{job.source}</Badge>
                        <a href={job.apply_url} target="_blank" rel="noreferrer" className="text-sm text-brand hover:underline inline-flex items-center gap-1">
                          <Link className="h-3.5 w-3.5" />
                          Apply URL
                        </a>
                      </div>

                      {job.description && <p className="text-muted-foreground line-clamp-2">{job.description}</p>}
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-2 items-end">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => void handleAutoApply(job.id)}
                    loading={applyingJobId === job.id}
                    disabled={!!applyingJobId}
                  >
                    <Zap className="h-4 w-4" />
                    Auto-Apply
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => void handleSaveJob(job.id)}
                    loading={jobUpdatingId === job.id && jobStatuses[job.id] !== 'dismissed'}
                    disabled={jobStatuses[job.id] === 'saved' || !!applyingJobId}
                  >
                    <Heart className="h-4 w-4" />
                    {jobStatuses[job.id] === 'saved' ? 'Saved' : 'Save'}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => void handleDismissJob(job.id)}
                    loading={jobUpdatingId === job.id && jobStatuses[job.id] !== 'saved'}
                    disabled={!!applyingJobId}
                  >
                    <X className="h-4 w-4" />
                    Dismiss
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
        )}

        {/* Pagination */}
        {!loadingFeed && total > 0 && (
          <div className="mt-6 flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Showing {skip + 1}-{Math.min(skip + itemsPerPage, total)} of {total}
            </p>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => void handlePageChange('prev')} disabled={!hasPrev || scanning || loadingFeed}>
                Previous
              </Button>
              <Button variant="outline" size="sm" onClick={() => void handlePageChange('next')} disabled={!hasNext || scanning || loadingFeed}>
                Next
              </Button>
            </div>
          </div>
        )}

        {/* Empty pre-scan state */}
        {!loadingFeed && jobs.length === 0 && !hasScanned && (
          <Card padding="lg" className="text-center">
            <RefreshCw className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">Ready for your first feed scan</h3>
            <p className="text-muted-foreground mb-6">
              Start by scanning configured job sources to build your personalized feed.
            </p>
            <Button variant="primary" onClick={() => void handleScanJobs()} loading={scanning}>
              Scan Job Feed
            </Button>
          </Card>
        )}

        {/* No new jobs found state */}
        {!loadingFeed && jobs.length === 0 && hasScanned && (
          <Card padding="lg" className="text-center">
            <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">No new jobs found</h3>
            <p className="text-muted-foreground mb-6">
              Try another scan, update preferences, or add a job manually.
            </p>
            <div className="flex items-center justify-center gap-3">
              <Button variant="outline" onClick={handleGoToPreferences}>
                Update Preferences
              </Button>
              <Button variant="primary" onClick={() => void handleScanJobs()} loading={scanning}>
                Scan for Jobs
              </Button>
            </div>
          </Card>
        )}
      </div>
    </AppShell>
  );
};
