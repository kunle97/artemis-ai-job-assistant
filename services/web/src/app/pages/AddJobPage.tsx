'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '../components/AppShell';
import { Button, Card, Input } from '../components/ui';
import { Plus, ArrowLeft } from 'lucide-react';
import { createJobFromUrl } from '../../services/jobs/job-feed.service';
import { getStoredAccessToken } from '../../services/auth/auth.service';

export const AddJobPage: React.FC = () => {
  const router = useRouter();
  const [jobUrl, setJobUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const token = getStoredAccessToken();

  const handleAddJob = async () => {
    if (!token) {
      setError('Please sign in to add a job.');
      return;
    }

    if (!jobUrl.trim()) {
      setError('Please enter a valid job URL.');
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const created = await createJobFromUrl(token, { apply_url: jobUrl.trim() });
      setMessage(`Successfully added "${created.title}" at ${created.company_name}.`);
      setJobUrl('');
      
      // Redirect back to feed after 2 seconds
      setTimeout(() => {
        router.push('/jobs/feed');
      }, 2000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unable to add job.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Button variant="ghost" onClick={() => router.push('/jobs')} className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Feed
          </Button>
          <h1 className="text-3xl font-semibold text-foreground">Add Job by URL</h1>
          <p className="mt-2 text-muted-foreground">
            Add a job posting that isn't yet in Artemis by pasting its application URL.
          </p>
        </div>

        {/* Form Card */}
        <Card padding="lg" variant="outlined">
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground block mb-2">Job URL</label>
              <Input
                type="url"
                placeholder="https://example.com/jobs/product-manager"
                value={jobUrl}
                onChange={(e) => setJobUrl(e.target.value)}
                fullWidth
                disabled={loading}
              />
              <p className="text-xs text-muted-foreground mt-2">
                Paste the full URL to the job application page.
              </p>
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}
            {message && <p className="text-sm text-brand">{message}</p>}

            <div className="flex gap-3 pt-4">
              <Button 
                variant="primary" 
                onClick={handleAddJob} 
                loading={loading}
              >
                <Plus className="h-4 w-4" />
                Add Job
              </Button>
            </div>
          </div>
        </Card>

        {/* Help Section */}
        <Card padding="md" variant="outlined" className="mt-8">
          <h2 className="text-base font-semibold text-foreground mb-3">Tips</h2>
          <ul className="space-y-2 text-sm text-muted-foreground list-disc list-inside">
            <li>Use the full job posting URL, not the company home page</li>
            <li>URLs from Greenhouse, Lever, Ashby, and other major ATSs work best</li>
            <li>The job will be added to your feed immediately</li>
            <li>You can save or dismiss it like any other job</li>
          </ul>
        </Card>
      </div>
    </AppShell>
  );
};
