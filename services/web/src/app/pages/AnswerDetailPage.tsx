"use client";

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { ArrowLeft, Save, Trash2 } from 'lucide-react';

import { AppShell } from '../components/AppShell';
import { Button, Card, CardContent, CardHeader, CardTitle, Input } from '../components/ui';
import { getStoredAccessToken } from '../../services/auth/auth.service';
import {
  listApplicationAnswers,
  saveApplicationAnswer,
  deleteApplicationAnswer,
  type ApplicationAnswer,
} from '../../services/applications/application-answers.service';

export const AnswerDetailPage: React.FC = () => {
  const router = useRouter();
  const params = useParams<{ answerId: string }>();
  const answerId = String(params?.answerId || '');
  const token = getStoredAccessToken();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [answer, setAnswer] = useState<ApplicationAnswer | null>(null);

  const [questionText, setQuestionText] = useState('');
  const [category, setCategory] = useState('');
  const [answerText, setAnswerText] = useState('');

  useEffect(() => {
    const load = async () => {
      if (!token) {
        setError('Please sign in to edit answers.');
        setLoading(false);
        return;
      }

      try {
        const results = await listApplicationAnswers(token);
        const target = results.find((item) => item.id === answerId) || null;

        if (!target) {
          setError('Answer not found.');
          setLoading(false);
          return;
        }

        setAnswer(target);
        setQuestionText(target.question_text || '');
        setCategory(target.category || '');
        setAnswerText(target.answer_text);
        setError(null);
      } catch (loadError) {
        const message = loadError instanceof Error ? loadError.message : 'Failed to load answer.';
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [answerId, token]);

  const handleSave = async () => {
    if (!token || !answer) return;

    const normalizedQuestionText = questionText.trim();
    const normalizedAnswerText = answerText.trim();

    if (!normalizedQuestionText) {
      toast.error('Question text is required');
      return;
    }

    if (!normalizedAnswerText) {
      toast.error('Answer text is required');
      return;
    }

    setSaving(true);
    try {
      const saved = await saveApplicationAnswer(token, {
        question_key: answer.question_key,
        question_text: normalizedQuestionText,
        category: category.trim() || null,
        answer_text: normalizedAnswerText,
      });

      setAnswer(saved);
      setQuestionText(saved.question_text || '');
      setCategory(saved.category || '');
      setAnswerText(saved.answer_text);

      toast.success('Answer updated', {
        description: 'Your changes have been saved.',
      });
    } catch (saveError) {
      const message = saveError instanceof Error ? saveError.message : 'Failed to save answer.';
      toast.error('Could not save answer', { description: message });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!token || !answer) return;
    setDeleting(true);
    try {
      await deleteApplicationAnswer(token, answer.id);
      toast.success('Answer deleted');
      router.push('/answers');
    } catch (deleteError) {
      const message = deleteError instanceof Error ? deleteError.message : 'Failed to delete answer.';
      toast.error('Could not delete answer', { description: message });
      setDeleting(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="text-3xl font-semibold text-foreground">Answer Details</h1>
            <p className="mt-2 text-muted-foreground">
              Review and edit this reusable answer.
            </p>
          </div>
          <Button variant="outline" onClick={() => router.push('/answers')}>
            <ArrowLeft className="h-4 w-4" />
            Back to Library
          </Button>
        </div>

        {loading && (
          <Card variant="outlined">
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">Loading answer details...</p>
            </CardContent>
          </Card>
        )}

        {!loading && error && (
          <Card variant="outlined" className="border-destructive/30 bg-destructive/5">
            <CardContent className="pt-6">
              <p className="text-sm text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {!loading && !error && answer && (
          <Card variant="outlined">
            <CardHeader>
              <CardTitle>Edit Reusable Answer</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                label="Question"
                value={questionText}
                onChange={(event) => setQuestionText(event.target.value)}
                fullWidth
              />
              <Input
                label="Category (optional)"
                value={category}
                onChange={(event) => setCategory(event.target.value)}
                fullWidth
              />
              <label className="grid gap-1.5 text-sm font-medium text-foreground">
                <span>Answer</span>
                <textarea
                  value={answerText}
                  onChange={(event) => setAnswerText(event.target.value)}
                  className="min-h-40 w-full rounded-md border border-input bg-input-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                />
              </label>
              <div className="flex justify-between items-center">
                <div className="flex gap-2">
                  {confirmDelete ? (
                    <>
                      <Button
                        variant="ghost"
                        className="text-destructive hover:text-destructive"
                        loading={deleting}
                        onClick={handleDelete}
                      >
                        Confirm Delete
                      </Button>
                      <Button variant="outline" onClick={() => setConfirmDelete(false)}>
                        Cancel
                      </Button>
                    </>
                  ) : (
                    <Button
                      variant="ghost"
                      className="text-muted-foreground hover:text-destructive"
                      onClick={() => setConfirmDelete(true)}
                    >
                      <Trash2 className="h-4 w-4" />
                      Delete
                    </Button>
                  )}
                </div>
                <Button variant="primary" onClick={handleSave} loading={saving}>
                  <Save className="h-4 w-4" />
                  Save Changes
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AppShell>
  );
};
