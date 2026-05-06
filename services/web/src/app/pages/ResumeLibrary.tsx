'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '../components/AppShell';
import { Button, Card, CardHeader, CardTitle, CardContent, Badge } from '../components/ui';
import { Upload, FileText, CheckCircle, AlertCircle, Download, Trash2 } from 'lucide-react';

interface Resume {
  id: string;
  filename: string;
  uploadedAt: string;
  status: 'parsed' | 'parsing' | 'error';
  extractedFields: number;
  totalFields: number;
}

const mockResumes: Resume[] = [
  {
    id: '1',
    filename: 'John_Doe_Resume_2026.pdf',
    uploadedAt: '2 days ago',
    status: 'parsed',
    extractedFields: 18,
    totalFields: 20,
  },
  {
    id: '2',
    filename: 'Product_Manager_Resume.pdf',
    uploadedAt: '1 week ago',
    status: 'parsed',
    extractedFields: 15,
    totalFields: 20,
  },
];

const mockMissingFields = [
  'GitHub Profile',
  'Portfolio Website',
];

export const ResumeLibrary: React.FC = () => {
  const router = useRouter();
  const [uploading, setUploading] = useState(false);

  const handleUpload = () => {
    setUploading(true);
    setTimeout(() => {
      setUploading(false);
    }, 2000);
  };

  const handleDownload = (id: string) => {
    alert(`Download resume ${id}`);
  };

  const handleDelete = (id: string) => {
    alert(`Delete resume ${id}`);
  };

  const handleFillMissingField = (field: string) => {
    router.push('/profile');
  };

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-semibold text-foreground">Resume Library</h1>
              <p className="mt-2 text-muted-foreground">
                Upload and manage your resumes. Artemis will parse them to auto-fill your profile.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Upload Area */}
            <Card padding="lg" className="border-2 border-dashed border-border hover:border-brand transition-colors">
              <div className="text-center">
                <div className="mx-auto h-16 w-16 rounded-full bg-brand/10 flex items-center justify-center mb-4">
                  <Upload className="h-8 w-8 text-brand" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">Upload Your Resume</h3>
                <p className="text-muted-foreground mb-6">
                  Drag and drop your resume here, or click to browse
                </p>
                <Button variant="primary" onClick={handleUpload} loading={uploading}>
                  <Upload className="h-4 w-4" />
                  Choose File
                </Button>
                <p className="mt-4 text-sm text-muted-foreground">
                  Supported formats: PDF, DOC, DOCX (Max 5MB)
                </p>
              </div>
            </Card>

            {/* Resume List */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-foreground">Your Resumes</h2>
              {mockResumes.map((resume) => (
                <Card key={resume.id} padding="md" variant="outlined">
                  <div className="flex items-start gap-4">
                    <div className="h-12 w-12 rounded-lg bg-brand/10 flex items-center justify-center flex-shrink-0">
                      <FileText className="h-6 w-6 text-brand" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="font-semibold text-foreground">{resume.filename}</h3>
                          <p className="text-sm text-muted-foreground">Uploaded {resume.uploadedAt}</p>
                        </div>
                        <Badge variant={resume.status === 'parsed' ? 'success' : 'warning'} size="sm">
                          {resume.status === 'parsed' ? 'Parsed' : 'Parsing...'}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 mb-3">
                        <div className="flex items-center gap-2">
                          <CheckCircle className="h-4 w-4 text-success" />
                          <span className="text-sm text-muted-foreground">
                            {resume.extractedFields} of {resume.totalFields} fields extracted
                          </span>
                        </div>
                        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-success"
                            style={{ width: `${(resume.extractedFields / resume.totalFields) * 100}%` }}
                          />
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={() => handleDownload(resume.id)}>
                          <Download className="h-4 w-4" />
                          Download
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(resume.id)}>
                          <Trash2 className="h-4 w-4" />
                          Delete
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {mockResumes.length === 0 && (
              <Card padding="lg" className="text-center">
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-foreground mb-2">No resumes uploaded</h3>
                <p className="text-muted-foreground mb-6">
                  Upload your first resume to get started with auto-fill
                </p>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Parsing Results */}
            <Card>
              <CardHeader>
                <CardTitle>Latest Parsing Result</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-success" />
                    <span className="text-foreground">Parsing completed successfully</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Fields extracted</span>
                      <span className="font-medium text-foreground">18 / 20</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Confidence</span>
                      <span className="font-medium text-foreground">92%</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Missing Fields */}
            {mockMissingFields.length > 0 && (
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <AlertCircle className="h-5 w-5 text-warning" />
                    <CardTitle>Missing Profile Fields</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    These fields couldn't be extracted from your resume. Fill them in manually for better results.
                  </p>
                  <div className="space-y-2">
                    {mockMissingFields.map((field) => (
                      <button
                        key={field}
                        onClick={() => handleFillMissingField(field)}
                        className="w-full flex items-center justify-between px-3 py-2 rounded-lg border border-border hover:bg-secondary transition-colors text-left"
                      >
                        <span className="text-sm text-foreground">{field}</span>
                        <span className="text-xs text-brand">Fill →</span>
                      </button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Tips */}
            <Card variant="outlined" className="bg-brand/5 border-brand/20">
              <CardHeader>
                <CardTitle>Tips for Best Results</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex gap-2">
                    <span>•</span>
                    <span>Use a standard resume format (PDF preferred)</span>
                  </li>
                  <li className="flex gap-2">
                    <span>•</span>
                    <span>Include clear section headers</span>
                  </li>
                  <li className="flex gap-2">
                    <span>•</span>
                    <span>Avoid images or complex layouts</span>
                  </li>
                  <li className="flex gap-2">
                    <span>•</span>
                    <span>Keep formatting simple and clean</span>
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
};
