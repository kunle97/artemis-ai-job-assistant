'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '../components/AppShell';
import { Button, Card, Input, Badge } from '../components/ui';
import { ArrowLeft, Save, AlertCircle, CheckCircle, Sparkles } from 'lucide-react';

interface UnresolvedField {
  id: string;
  fieldName: string;
  question: string;
  suggestedAnswer: string | null;
  required: boolean;
  userAnswer: string;
}

const mockUnresolvedFields: UnresolvedField[] = [
  {
    id: '1',
    fieldName: 'Cover Letter',
    question: 'Please provide a cover letter for this position',
    suggestedAnswer: null,
    required: true,
    userAnswer: '',
  },
  {
    id: '2',
    fieldName: 'Salary Expectations',
    question: 'What are your salary expectations for this role?',
    suggestedAnswer: '$150,000 - $200,000',
    required: false,
    userAnswer: '',
  },
  {
    id: '3',
    fieldName: 'Start Date',
    question: 'When can you start?',
    suggestedAnswer: null,
    required: true,
    userAnswer: '',
  },
  {
    id: '4',
    fieldName: 'Why this company?',
    question: 'Why do you want to work for TechCorp specifically?',
    suggestedAnswer: "I am excited about TechCorp's mission to transform how teams collaborate. I have followed your journey since the Series A and am impressed by how you've maintained product quality while scaling rapidly.",
    required: false,
    userAnswer: '',
  },
];

export const ManualReviewPanel: React.FC = () => {
  const router = useRouter();
  const [fields, setFields] = useState(mockUnresolvedFields);
  const [saving, setSaving] = useState(false);

  const handleFieldChange = (id: string, value: string) => {
    setFields(fields.map((f) => (f.id === id ? { ...f, userAnswer: value } : f)));
  };

  const handleUseSuggestion = (id: string) => {
    const field = fields.find((f) => f.id === id);
    if (field?.suggestedAnswer) {
      setFields(fields.map((f) => (f.id === id ? { ...f, userAnswer: field.suggestedAnswer! } : f)));
    }
  };

  const handleSave = () => {
    setSaving(true);
    setTimeout(() => {
      setSaving(false);
      router.push('/applications/1');
    }, 1500);
  };

  const handleBack = () => {
    router.push('/applications/1');
  };

  const requiredFieldsFilled = fields
    .filter((f) => f.required)
    .every((f) => f.userAnswer.trim().length > 0);

  const totalFields = fields.length;
  const filledFields = fields.filter((f) => f.userAnswer.trim().length > 0).length;

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-4"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Application
          </button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-semibold text-foreground">Manual Review Required</h1>
              <p className="mt-1 text-muted-foreground">
                Senior Product Manager at TechCorp Inc.
              </p>
            </div>
            <Badge variant={requiredFieldsFilled ? 'success' : 'warning'}>
              {filledFields} of {totalFields} resolved
            </Badge>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Info Banner */}
            <Card variant="outlined" className="bg-info/5 border-info/20">
              <div className="flex gap-3 p-4">
                <AlertCircle className="h-5 w-5 text-info flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-foreground mb-1">
                    These fields need your attention
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Artemis couldn't auto-fill these fields. Please provide answers manually or use the suggested responses where available.
                  </p>
                </div>
              </div>
            </Card>

            {/* Unresolved Fields */}
            <div className="space-y-6">
              {fields.map((field) => (
                <Card key={field.id} padding="md" variant="outlined">
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold text-foreground flex items-center gap-2">
                          {field.fieldName}
                          {field.required && (
                            <Badge variant="danger" size="sm">
                              Required
                            </Badge>
                          )}
                        </h3>
                        <p className="text-sm text-muted-foreground mt-1">{field.question}</p>
                      </div>
                    </div>

                    {field.suggestedAnswer && (
                      <div className="p-3 rounded-lg bg-brand/5 border border-brand/20">
                        <div className="flex items-start gap-2 mb-2">
                          <Sparkles className="h-4 w-4 text-brand flex-shrink-0 mt-0.5" />
                          <p className="text-sm font-medium text-foreground">Suggested Answer</p>
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">{field.suggestedAnswer}</p>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleUseSuggestion(field.id)}
                        >
                          Use This Answer
                        </Button>
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Your Answer
                      </label>
                      <textarea
                        value={field.userAnswer}
                        onChange={(e) => handleFieldChange(field.id, e.target.value)}
                        placeholder="Enter your answer here..."
                        rows={4}
                        className="w-full px-4 py-2 rounded-lg border border-border bg-input-background focus:ring-2 focus:ring-brand focus:border-brand resize-y"
                      />
                    </div>

                    {field.userAnswer.trim().length > 0 && (
                      <div className="flex items-center gap-2 text-success">
                        <CheckCircle className="h-4 w-4" />
                        <span className="text-sm">Answer provided</span>
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Progress */}
            <Card>
              <div className="p-4 space-y-4">
                <div>
                  <h3 className="font-semibold text-foreground mb-2">Progress</h3>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-3 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-brand transition-all duration-300"
                        style={{ width: `${(filledFields / totalFields) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-foreground">
                      {Math.round((filledFields / totalFields) * 100)}%
                    </span>
                  </div>
                </div>

                <div className="space-y-2 pt-4 border-t border-border">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Total fields</span>
                    <span className="font-medium text-foreground">{totalFields}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Resolved</span>
                    <span className="font-medium text-foreground">{filledFields}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Remaining</span>
                    <span className="font-medium text-foreground">{totalFields - filledFields}</span>
                  </div>
                </div>
              </div>
            </Card>

            {/* Actions */}
            <Card>
              <div className="p-4 space-y-3">
                <h3 className="font-semibold text-foreground mb-2">Actions</h3>
                <Button
                  variant="primary"
                  fullWidth
                  onClick={handleSave}
                  loading={saving}
                  disabled={!requiredFieldsFilled}
                >
                  <Save className="h-4 w-4" />
                  Save & Continue
                </Button>
                {!requiredFieldsFilled && (
                  <p className="text-xs text-muted-foreground text-center">
                    Fill all required fields to continue
                  </p>
                )}
                <Button variant="outline" fullWidth onClick={handleBack}>
                  Save Draft
                </Button>
              </div>
            </Card>

            {/* Tips */}
            <Card variant="outlined" className="bg-muted/30">
              <div className="p-4">
                <h3 className="font-semibold text-foreground mb-3">Tips</h3>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex gap-2">
                    <span>•</span>
                    <span>Use suggested answers as a starting point and customize them</span>
                  </li>
                  <li className="flex gap-2">
                    <span>•</span>
                    <span>Save good answers to your library for reuse</span>
                  </li>
                  <li className="flex gap-2">
                    <span>•</span>
                    <span>Required fields must be filled before submission</span>
                  </li>
                </ul>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
};
