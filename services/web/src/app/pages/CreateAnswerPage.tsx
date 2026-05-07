"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { ArrowLeft, Save } from 'lucide-react';

import { AppShell } from '../components/AppShell';
import { Button, Card, CardContent, CardHeader, CardTitle, Input } from '../components/ui';
import { getStoredAccessToken } from '../../services/auth/auth.service';
import {
  buildApplicationAnswerQuestionKey,
  saveApplicationAnswer,
} from '../../services/applications/application-answers.service';

export const CreateAnswerPage: React.FC = () => {
  const router = useRouter();
  const token = getStoredAccessToken();

  const [questionText, setQuestionText] = useState('');
  const [category, setCategory] = useState('');
  const [answerText, setAnswerText] = useState('');
  const [saving, setSaving] = useState(false);

  const handleCreate = async () => {
    if (!token) {
      toast.error('Please sign in to create answers.');
      return;
    }

    const normalizedQuestionText = questionText.trim();
    const normalizedAnswerText = answerText.trim();
    const questionKey = buildApplicationAnswerQuestionKey(normalizedQuestionText);

    if (!normalizedQuestionText) {
      toast.error('Question text is required');
      return;
    }

    if (!normalizedAnswerText) {
      toast.error('Answer text is required');
      return;
    }

    if (!questionKey) {
      toast.error('Unable to generate question key from this question.');
      return;
    }

    setSaving(true);
    try {
      const saved = await saveApplicationAnswer(token, {
        question_key: questionKey,
        question_text: normalizedQuestionText,
        category: category.trim() || null,
        answer_text: normalizedAnswerText,
      });

      toast.success('Answer created', {
        description: 'Your reusable answer has been added to your library.',
      });
      router.push(`/answers/${saved.id}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create answer.';
      toast.error('Could not create answer', { description: message });
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="text-3xl font-semibold text-foreground">Create Reusable Answer</h1>
            <p className="mt-2 text-muted-foreground">
              Save a high-quality response once so Artemis can reuse it across applications.
            </p>
          </div>
          <Button variant="outline" onClick={() => router.push('/answers')}>
            <ArrowLeft className="h-4 w-4" />
            Back to Library
          </Button>
        </div>

        <Card variant="outlined">
          <CardHeader>
            <CardTitle>Answer Content</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Question"
              value={questionText}
              onChange={(event) => setQuestionText(event.target.value)}
              placeholder="e.g. Why do you want to work here?"
              fullWidth
            />
            <Input
              label="Category (optional)"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              placeholder="e.g. Motivation"
              fullWidth
            />
            <label className="grid gap-1.5 text-sm font-medium text-foreground">
              <span>Answer</span>
              <textarea
                value={answerText}
                onChange={(event) => setAnswerText(event.target.value)}
                placeholder="Write your reusable answer..."
                className="min-h-40 w-full rounded-md border border-input bg-input-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
              />
            </label>
            <div className="flex justify-end">
              <Button variant="primary" onClick={handleCreate} loading={saving}>
                <Save className="h-4 w-4" />
                Create Answer
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
};
