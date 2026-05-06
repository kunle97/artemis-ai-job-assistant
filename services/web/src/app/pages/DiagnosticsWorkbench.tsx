'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Card, CardHeader, CardTitle, CardContent, Badge } from '../components/ui';
import { Play, Terminal, FileCode, AlertTriangle, CheckCircle, ArrowLeft } from 'lucide-react';

export const DiagnosticsWorkbench: React.FC = () => {
  const router = useRouter();
  const [selectedTab, setSelectedTab] = useState<'inspection' | 'fill-plan' | 'test-fill' | 'logs'>('inspection');
  const [running, setRunning] = useState(false);

  const handleRun = () => {
    setRunning(true);
    setTimeout(() => {
      setRunning(false);
    }, 2000);
  };

  const handleBack = () => {
    router.push('/jobs');
  };

  const mockInspectionOutput = {
    url: 'https://techcorp.com/careers/apply/12345',
    formFields: [
      { name: 'firstName', type: 'text', required: true, detected: true },
      { name: 'lastName', type: 'text', required: true, detected: true },
      { name: 'email', type: 'email', required: true, detected: true },
      { name: 'resume', type: 'file', required: true, detected: true },
      { name: 'coverLetter', type: 'textarea', required: false, detected: false },
      { name: 'linkedin', type: 'url', required: false, detected: true },
    ],
    detectionConfidence: 87,
  };

  const mockFillPlan = [
    { field: 'firstName', source: 'profile.firstName', value: 'John', confidence: 100 },
    { field: 'lastName', source: 'profile.lastName', value: 'Doe', confidence: 100 },
    { field: 'email', source: 'profile.email', value: 'john@example.com', confidence: 100 },
    { field: 'resume', source: 'resume.latest', value: 'John_Doe_Resume.pdf', confidence: 100 },
    { field: 'coverLetter', source: null, value: null, confidence: 0 },
    { field: 'linkedin', source: 'profile.linkedin', value: 'https://linkedin.com/in/johndoe', confidence: 100 },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="mx-auto max-w-7xl px-6 py-4">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-4"
          >
            <ArrowLeft className="h-4 w-4" />
            Exit Diagnostics
          </button>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3">
                <Terminal className="h-8 w-8 text-destructive" />
                <div>
                  <h1 className="text-2xl font-semibold text-foreground">Automation Diagnostics Workbench</h1>
                  <p className="text-sm text-muted-foreground">Internal debugging and QA tool</p>
                </div>
              </div>
            </div>
            <Badge variant="danger">Internal Only</Badge>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        {/* Warning Banner */}
        <Card variant="outlined" className="mb-6 bg-destructive/5 border-destructive/20">
          <div className="flex gap-3 p-4">
            <AlertTriangle className="h-5 w-5 text-destructive flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-foreground">Internal Tool</p>
              <p className="text-sm text-muted-foreground">
                This workbench is for debugging automation workflows. It is not intended for candidate use.
              </p>
            </div>
          </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar - Test Controls */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Test Controls</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Application ID</label>
                  <input
                    type="text"
                    defaultValue="app-12345"
                    className="w-full px-3 py-2 rounded-lg border border-border bg-input-background text-foreground"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Target URL</label>
                  <input
                    type="text"
                    defaultValue="https://techcorp.com/careers/apply/12345"
                    className="w-full px-3 py-2 rounded-lg border border-border bg-input-background text-foreground"
                  />
                </div>
                <Button variant="primary" fullWidth onClick={handleRun} loading={running}>
                  <Play className="h-4 w-4" />
                  Run Test
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button variant="outline" size="sm" fullWidth>
                  Clear Cache
                </Button>
                <Button variant="outline" size="sm" fullWidth>
                  Reset State
                </Button>
                <Button variant="outline" size="sm" fullWidth>
                  Export Logs
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {/* Tabs */}
            <Card padding="none">
              <div className="border-b border-border">
                <div className="flex">
                  {[
                    { key: 'inspection', label: 'Inspection Output' },
                    { key: 'fill-plan', label: 'Fill Plan' },
                    { key: 'test-fill', label: 'Test Fill Results' },
                    { key: 'logs', label: 'Debug Logs' },
                  ].map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => setSelectedTab(tab.key as any)}
                      className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                        selectedTab === tab.key
                          ? 'border-brand text-brand'
                          : 'border-transparent text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-6">
                {/* Inspection Output Tab */}
                {selectedTab === 'inspection' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold text-foreground">Form Inspection Results</h3>
                      <Badge variant="success">
                        {mockInspectionOutput.detectionConfidence}% confidence
                      </Badge>
                    </div>
                    <div className="space-y-2">
                      <p className="text-sm text-muted-foreground">
                        URL: <code className="px-2 py-1 bg-muted rounded text-foreground">{mockInspectionOutput.url}</code>
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Fields detected: {mockInspectionOutput.formFields.length}
                      </p>
                    </div>
                    <div className="mt-4">
                      <table className="w-full">
                        <thead className="border-b border-border">
                          <tr>
                            <th className="text-left py-2 text-sm font-medium text-muted-foreground">Field Name</th>
                            <th className="text-left py-2 text-sm font-medium text-muted-foreground">Type</th>
                            <th className="text-left py-2 text-sm font-medium text-muted-foreground">Required</th>
                            <th className="text-left py-2 text-sm font-medium text-muted-foreground">Detected</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                          {mockInspectionOutput.formFields.map((field, index) => (
                            <tr key={index}>
                              <td className="py-2 text-sm font-mono text-foreground">{field.name}</td>
                              <td className="py-2 text-sm text-muted-foreground">{field.type}</td>
                              <td className="py-2">
                                {field.required ? (
                                  <Badge variant="warning" size="sm">Yes</Badge>
                                ) : (
                                  <span className="text-sm text-muted-foreground">No</span>
                                )}
                              </td>
                              <td className="py-2">
                                {field.detected ? (
                                  <CheckCircle className="h-4 w-4 text-success" />
                                ) : (
                                  <AlertTriangle className="h-4 w-4 text-destructive" />
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Fill Plan Tab */}
                {selectedTab === 'fill-plan' && (
                  <div className="space-y-4">
                    <h3 className="font-semibold text-foreground mb-4">Generated Fill Plan</h3>
                    <div className="space-y-3">
                      {mockFillPlan.map((plan, index) => (
                        <div key={index} className="p-3 rounded-lg border border-border">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <p className="font-mono text-sm font-medium text-foreground">{plan.field}</p>
                              <p className="text-xs text-muted-foreground">
                                {plan.source ? `Source: ${plan.source}` : 'No source available'}
                              </p>
                            </div>
                            <Badge variant={plan.confidence === 100 ? 'success' : plan.confidence > 0 ? 'warning' : 'danger'} size="sm">
                              {plan.confidence}%
                            </Badge>
                          </div>
                          {plan.value && (
                            <div className="mt-2 px-2 py-1 bg-muted rounded">
                              <code className="text-sm text-foreground">{plan.value}</code>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Test Fill Results Tab */}
                {selectedTab === 'test-fill' && (
                  <div className="space-y-4">
                    <h3 className="font-semibold text-foreground mb-4">Test Fill Results</h3>
                    <div className="p-4 rounded-lg bg-success/10 border border-success/20">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="h-5 w-5 text-success" />
                        <p className="font-medium text-foreground">Fill completed successfully</p>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        6 fields filled, 0 errors, 1 warning (cover letter not provided)
                      </p>
                    </div>
                    <div className="mt-4 p-4 rounded-lg bg-muted">
                      <p className="text-xs font-mono text-muted-foreground whitespace-pre">
{`Execution time: 2.3s
Fields filled: 6/7
Success rate: 85.7%
Warnings: 1
Errors: 0`}
                      </p>
                    </div>
                  </div>
                )}

                {/* Debug Logs Tab */}
                {selectedTab === 'logs' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold text-foreground">Debug Logs</h3>
                      <Button variant="outline" size="sm">
                        <FileCode className="h-4 w-4" />
                        Export
                      </Button>
                    </div>
                    <div className="p-4 rounded-lg bg-foreground text-background font-mono text-xs overflow-x-auto max-h-96 overflow-y-auto">
                      <div className="space-y-1">
                        <p>[2026-05-05 10:23:15] INFO: Starting automation workflow</p>
                        <p>[2026-05-05 10:23:15] INFO: Loading application data (app-12345)</p>
                        <p>[2026-05-05 10:23:16] INFO: Inspecting target form at https://techcorp.com/careers/apply/12345</p>
                        <p>[2026-05-05 10:23:17] INFO: Detected 6 form fields</p>
                        <p>[2026-05-05 10:23:17] INFO: Generating fill plan</p>
                        <p>[2026-05-05 10:23:18] INFO: Matched 5/6 fields from profile</p>
                        <p className="text-yellow-300">[2026-05-05 10:23:18] WARN: No source found for field: coverLetter</p>
                        <p>[2026-05-05 10:23:18] INFO: Executing fill plan</p>
                        <p>[2026-05-05 10:23:19] INFO: Filled field: firstName</p>
                        <p>[2026-05-05 10:23:19] INFO: Filled field: lastName</p>
                        <p>[2026-05-05 10:23:20] INFO: Filled field: email</p>
                        <p>[2026-05-05 10:23:20] INFO: Uploaded file: resume</p>
                        <p>[2026-05-05 10:23:21] INFO: Filled field: linkedin</p>
                        <p className="text-green-300">[2026-05-05 10:23:21] INFO: Automation completed successfully</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
};
