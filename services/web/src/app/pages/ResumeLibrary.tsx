'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '../components/AppShell';
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from '../components/ui';
import { AlertCircle, CheckCircle, FileText, Loader2, Trash2, Upload } from 'lucide-react';
import { getStoredAccessToken } from '../../services/auth/auth.service';
import {
  deleteResume,
  getResumes,
  setPrimaryResume,
  uploadResume,
  type ResumeRead,
  type ResumeUploadResponse,
} from '../../services/resumes/resume.service';

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Unknown upload time';

  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

export const ResumeLibrary: React.FC = () => {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isDragOver, setIsDragOver] = useState(false);
  const [resumes, setResumes] = useState<ResumeRead[]>([]);
  const [loadingResumes, setLoadingResumes] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadingFileName, setUploadingFileName] = useState<string>('');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deletingResumeId, setDeletingResumeId] = useState<string | null>(null);
  const [settingPrimaryResumeId, setSettingPrimaryResumeId] = useState<string | null>(null);
  const [latestUpload, setLatestUpload] = useState<ResumeUploadResponse | null>(null);

  const loadResumes = useCallback(async () => {
    const token = getStoredAccessToken();
    if (!token) {
      router.push('/signin');
      return;
    }

    setLoadError(null);

    try {
      const list = await getResumes(token);
      setResumes(list);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : 'Unable to load resumes.');
    } finally {
      setLoadingResumes(false);
    }
  }, [router]);

  useEffect(() => {
    void loadResumes();
  }, [loadResumes]);

  const missingFields = latestUpload?.missing_profile_fields ?? [];
  const hasPartialParse = missingFields.length > 0;

  const latestResume = useMemo(() => {
    if (resumes.length === 0) return null;
    return resumes[0];
  }, [resumes]);

  const defaultResume = useMemo(() => {
    if (resumes.length === 0) return null;
    return resumes.find((resume) => resume.is_primary) || resumes[0];
  }, [resumes]);

  const handleGoToProfile = () => {
    router.push('/profile');
  };

  const handleResumeUpload = async (file: File) => {
    const token = getStoredAccessToken();
    if (!token) {
      router.push('/signin');
      return;
    }

    setUploading(true);
    setUploadingFileName(file.name);
    setUploadError(null);
    setDeleteError(null);

    try {
      const response = await uploadResume(file, token);
      setLatestUpload(response);
      await loadResumes();
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Resume upload failed.');
    } finally {
      setUploading(false);
      setUploadingFileName('');
    }
  };

  const handleFileSelection = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    await handleResumeUpload(file);
    event.target.value = '';
  };

  const handleDrop = async (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);

    const file = event.dataTransfer.files?.[0];
    if (!file) return;
    await handleResumeUpload(file);
  };

  const handleDeleteResume = async (resumeId: string) => {
    const token = getStoredAccessToken();
    if (!token) {
      router.push('/signin');
      return;
    }

    setDeleteError(null);
    setDeletingResumeId(resumeId);

    try {
      await deleteResume(resumeId, token);
      if (latestUpload?.id === resumeId) {
        setLatestUpload(null);
      }
      await loadResumes();
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : 'Unable to delete resume.');
    } finally {
      setDeletingResumeId(null);
    }
  };

  const handleSetPrimaryResume = async (resumeId: string) => {
    const token = getStoredAccessToken();
    if (!token) {
      router.push('/signin');
      return;
    }

    setDeleteError(null);
    setUploadError(null);
    setSettingPrimaryResumeId(resumeId);

    try {
      await setPrimaryResume(resumeId, token);
      await loadResumes();
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : 'Unable to update default resume.');
    } finally {
      setSettingPrimaryResumeId(null);
    }
  };

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-semibold text-foreground">Resume Library</h1>
          <p className="mt-2 text-muted-foreground">
            Upload resumes, review parsed output, and complete any profile gaps before automation runs.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Upload Resume</CardTitle>
              </CardHeader>
              <CardContent>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.doc,.docx,.txt"
                  className="hidden"
                  onChange={handleFileSelection}
                />

                <div
                  className={`rounded-xl border-2 border-dashed p-6 text-center transition-colors ${
                    isDragOver ? 'border-brand bg-brand/5' : 'border-border hover:border-brand'
                  } ${uploading ? 'relative overflow-hidden cursor-wait' : ''}`}
                  onDragOver={(event) => {
                    if (uploading) return;
                    event.preventDefault();
                    setIsDragOver(true);
                  }}
                  onDragEnter={(event) => {
                    if (uploading) return;
                    event.preventDefault();
                    setIsDragOver(true);
                  }}
                  onDragLeave={() => setIsDragOver(false)}
                  onDrop={handleDrop}
                >
                  {uploading && (
                    <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-2 bg-background/85 backdrop-blur-sm">
                      <Loader2 className="h-6 w-6 animate-spin text-brand" />
                      <p className="text-sm font-medium text-foreground">Uploading and parsing resume...</p>
                      <p className="text-xs text-muted-foreground max-w-[80%] truncate">{uploadingFileName}</p>
                    </div>
                  )}

                  <div className="mx-auto h-14 w-14 rounded-full bg-brand/10 flex items-center justify-center mb-4">
                    {uploading ? (
                      <Loader2 className="h-7 w-7 text-brand animate-spin" />
                    ) : (
                      <Upload className="h-7 w-7 text-brand" />
                    )}
                  </div>
                  <h3 className="text-lg font-semibold text-foreground">Upload a new resume</h3>
                  <p className="text-sm text-muted-foreground mt-2">
                    Drag and drop a file, or browse from your computer.
                  </p>
                  <div className="mt-5 flex justify-center">
                    <Button
                      variant="primary"
                      loading={uploading}
                      disabled={uploading}
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <Upload className="h-4 w-4" />
                      Choose File
                    </Button>
                  </div>
                  <p className="mt-4 text-xs text-muted-foreground">Supported: PDF, DOCX, TXT</p>
                </div>

                {uploadError && (
                  <div className="mt-4 flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-destructive">
                    <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                    <p className="text-sm">{uploadError}</p>
                  </div>
                )}

                {deleteError && (
                  <div className="mt-4 flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-destructive">
                    <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                    <p className="text-sm">{deleteError}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {latestUpload && (
              <Card>
                <CardHeader>
                  <CardTitle>Latest Upload Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-foreground">{latestUpload.file_name}</p>
                      <p className="text-sm text-muted-foreground">{latestUpload.message}</p>
                    </div>
                    <Badge variant={hasPartialParse ? 'warning' : 'success'} size="sm">
                      {hasPartialParse ? 'Partial Parse' : 'Parsed'}
                    </Badge>
                  </div>

                  {missingFields.length > 0 && (
                    <div className="rounded-lg border border-warning/30 bg-warning/10 p-3">
                      <p className="text-sm text-foreground font-medium mb-2">Missing profile fields detected</p>
                      <ul className="list-disc pl-5 space-y-1">
                        {missingFields.map((field) => (
                          <li key={field} className="text-sm text-muted-foreground">
                            {field}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle>Your Resumes</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {loadingResumes && <div className="text-sm text-muted-foreground">Loading resume library...</div>}

                {!loadingResumes && loadError && (
                  <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-destructive">
                    <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                    <p className="text-sm">{loadError}</p>
                  </div>
                )}

                {!loadingResumes && !loadError && resumes.length === 0 && (
                  <div className="rounded-xl border border-border p-6 text-center">
                    <FileText className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
                    <p className="text-foreground font-medium">No resumes uploaded yet</p>
                    <p className="text-sm text-muted-foreground mt-1 mb-4">
                      Upload your first resume to start profile autofill and readiness scoring.
                    </p>
                    <Button variant="outline" onClick={() => fileInputRef.current?.click()}>
                      <Upload className="h-4 w-4" />
                      Upload First Resume
                    </Button>
                  </div>
                )}

                {!loadingResumes && !loadError && resumes.length > 0 && (
                  <div className="space-y-3">
                    {resumes.map((resume) => {
                      const statusText = resume.parsed_json?.status?.trim().toLowerCase() ?? 'uploaded';
                      const parsed = statusText === 'success' || Boolean(resume.parsed_json?.normalized_data);

                      return (
                        <div key={resume.id} className="rounded-xl border border-border p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex items-start gap-3 min-w-0">
                              <div className="h-10 w-10 rounded-lg bg-brand/10 flex items-center justify-center shrink-0">
                                <FileText className="h-5 w-5 text-brand" />
                              </div>
                              <div className="min-w-0">
                                <p className="font-medium text-foreground truncate">{resume.file_name}</p>
                                <p className="text-xs text-muted-foreground mt-1">
                                  Uploaded {formatTimestamp(resume.created_at)}
                                </p>
                                <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                                  <span>{resume.mime_type || 'Unknown format'} • {resume.variant_type}</span>
                                  {resume.is_primary ? <Badge variant="success" size="sm">Default</Badge> : null}
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge variant={parsed ? 'success' : 'warning'} size="sm">
                                {parsed ? 'Parsed' : 'Uploaded'}
                              </Badge>
                              <Button
                                variant="outline"
                                size="sm"
                                loading={settingPrimaryResumeId === resume.id}
                                disabled={Boolean(settingPrimaryResumeId) || resume.is_primary}
                                onClick={() => handleSetPrimaryResume(resume.id)}
                              >
                                {resume.is_primary ? 'Default Resume' : 'Set as Default'}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                loading={deletingResumeId === resume.id}
                                disabled={Boolean(deletingResumeId)}
                                onClick={() => handleDeleteResume(resume.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                                Delete
                              </Button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Automation Readiness</CardTitle>
              </CardHeader>
              <CardContent>
                {!latestUpload && (
                  <p className="text-sm text-muted-foreground">
                    Upload a resume to see parsing status and profile completion guidance.
                  </p>
                )}

                {latestUpload && !hasPartialParse && (
                  <div className="flex items-start gap-2 text-success">
                    <CheckCircle className="h-5 w-5 mt-0.5" />
                    <div>
                      <p className="font-medium text-foreground">Profile data extracted cleanly</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        Your latest resume parse did not report missing profile fields.
                      </p>
                    </div>
                  </div>
                )}

                {latestUpload && hasPartialParse && (
                  <div className="space-y-3">
                    <div className="flex items-start gap-2 text-warning">
                      <AlertCircle className="h-5 w-5 mt-0.5" />
                      <div>
                        <p className="font-medium text-foreground">Manual completion recommended</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          Fill missing profile fields to improve autofill and application quality.
                        </p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      {missingFields.map((field) => (
                        <div key={field} className="text-sm rounded-md border border-border px-3 py-2 text-foreground">
                          {field}
                        </div>
                      ))}
                    </div>
                    <Button variant="outline" fullWidth onClick={handleGoToProfile}>
                      Complete Profile Fields
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card variant="outlined" className="bg-brand/5 border-brand/20">
              <CardHeader>
                <CardTitle>Tips for Best Results</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex gap-2">
                    <span>•</span>
                    <span>Use PDF or DOCX when possible</span>
                  </li>
                  <li className="flex gap-2">
                    <span>•</span>
                    <span>Use a clean single-column layout where possible</span>
                  </li>
                  <li className="flex gap-2">
                    <span>•</span>
                    <span>Keep section headers explicit: Experience, Education, Skills</span>
                  </li>
                  <li className="flex gap-2">
                    <span>•</span>
                    <span>Ensure LinkedIn and GitHub links appear in your header</span>
                  </li>
                </ul>
              </CardContent>
            </Card>

            {defaultResume && (
              <Card>
                <CardHeader>
                  <CardTitle>Default Resume</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="font-medium text-foreground">{defaultResume.file_name}</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Used by default when creating applications and opening resume tailoring.
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">Uploaded {formatTimestamp(defaultResume.created_at)}</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
};
