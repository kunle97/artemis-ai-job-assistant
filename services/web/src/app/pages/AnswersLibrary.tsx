import React, { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { AppShell } from '../components/AppShell';
import { Button, Card, CardHeader, CardTitle, CardContent, Input } from '../components/ui';
import { Plus, Search, Edit, BookOpen, Sparkles, Trash2 } from 'lucide-react';
import { getStoredAccessToken } from '../../services/auth/auth.service';
import {
  listApplicationAnswers,
  deleteApplicationAnswer,
  resolveApplicationAnswer,
  type ApplicationAnswer,
  type ApplicationAnswerResolution,
} from '../../services/applications/application-answers.service';

const SOURCE_LABELS: Record<string, string> = {
  saved_answer_exact: 'Exact saved answer',
  saved_answer_fuzzy: 'Fuzzy saved answer',
  user_intent_answer: 'Intent-based saved answer',
  default_intent_answer: 'Default intent answer',
  unresolved: 'No strong match',
};

const PAGE_SIZE = 8;

export const AnswersLibrary: React.FC = () => {
  const router = useRouter();
  const [answers, setAnswers] = useState<ApplicationAnswer[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const [testQuestion, setTestQuestion] = useState('');
  const [resolving, setResolving] = useState(false);
  const [resolution, setResolution] = useState<ApplicationAnswerResolution | null>(null);
  const [resolutionError, setResolutionError] = useState<string | null>(null);

  const token = getStoredAccessToken();

  const handleDelete = async (answerId: string) => {
    if (!token) return;
    setDeletingId(answerId);
    try {
      await deleteApplicationAnswer(token, answerId);
      setAnswers((prev) => prev.filter((a) => a.id !== answerId));
      setConfirmDeleteId(null);
      toast.success('Answer deleted');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete answer.';
      toast.error('Could not delete answer', { description: message });
    } finally {
      setDeletingId(null);
    }
  };

  useEffect(() => {
    const load = async () => {
      if (!token) {
        setLoadError('Please sign in to manage your reusable answers.');
        setLoading(false);
        return;
      }

      try {
        const data = await listApplicationAnswers(token);
        setAnswers(data);
        setLoadError(null);
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to load answers.';
        setLoadError(message);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [token]);

  const filteredAnswers = useMemo(
    () =>
      answers.filter(
    (answer) =>
        (answer.question_text || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        answer.answer_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (answer.category || '').toLowerCase().includes(searchQuery.toLowerCase()),
      ),
    [answers, searchQuery],
  );

  const totalPages = Math.max(1, Math.ceil(filteredAnswers.length / PAGE_SIZE));
  const paginatedAnswers = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return filteredAnswers.slice(start, start + PAGE_SIZE);
  }, [currentPage, filteredAnswers]);

  const categories = useMemo(
    () => Array.from(new Set(answers.map((a) => a.category).filter(Boolean))) as string[],
    [answers],
  );

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery]);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  const handleTestMatch = async () => {
    if (!token || !testQuestion.trim()) return;
    setResolving(true);
    setResolutionError(null);

    try {
      const result = await resolveApplicationAnswer(token, testQuestion.trim());
      setResolution(result);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to resolve question.';
      setResolutionError(message);
      setResolution(null);
    } finally {
      setResolving(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-semibold text-foreground">Answers Library</h1>
              <p className="mt-2 text-muted-foreground">
                Build a reusable knowledge base of your best application answers and test how Artemis resolves prompts.
              </p>
            </div>
            <Button variant="primary" onClick={() => router.push('/answers/new')}>
              <Plus className="h-4 w-4" />
              Create Answer
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Search */}
            <Card padding="sm" variant="outlined">
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-input-background border border-border">
                <Search className="h-5 w-5 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search your answers..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 bg-transparent border-none outline-none text-foreground placeholder:text-muted-foreground"
                />
              </div>
            </Card>

            {loading && (
              <Card padding="md" variant="outlined">
                <p className="text-sm text-muted-foreground">Loading saved answers...</p>
              </Card>
            )}

            {loadError && !loading && (
              <Card padding="md" className="border-destructive/30 bg-destructive/5">
                <p className="text-sm text-destructive">{loadError}</p>
              </Card>
            )}

            {/* Answers List */}
            <div className="space-y-4">
              {paginatedAnswers.map((answer) => (
                <Card key={answer.id} padding="md" variant="outlined">
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex items-start gap-3 flex-1">
                      <BookOpen className="h-5 w-5 text-brand flex-shrink-0 mt-1" />
                      <div className="flex-1">
                        <h3 className="font-semibold text-foreground mb-1">
                          {answer.question_text || 'Saved reusable answer'}
                        </h3>
                        <div className="flex items-center gap-2 mb-3">
                          {answer.category ? (
                            <span className="text-xs px-2 py-1 rounded-full bg-brand/10 text-brand font-medium">
                              {answer.category}
                            </span>
                          ) : null}
                          <span className="text-xs text-muted-foreground">
                            Updated {new Date(answer.updated_at).toLocaleDateString()}
                          </span>
                        </div>
                        <p className="text-muted-foreground leading-relaxed whitespace-pre-wrap break-words max-h-24 overflow-hidden">
                          {answer.answer_text}
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => router.push(`/answers/${answer.id}`)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      {confirmDeleteId === answer.id ? (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-destructive hover:text-destructive"
                            loading={deletingId === answer.id}
                            onClick={() => handleDelete(answer.id)}
                          >
                            Confirm
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setConfirmDeleteId(null)}
                          >
                            Cancel
                          </Button>
                        </>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-muted-foreground hover:text-destructive"
                          onClick={() => setConfirmDeleteId(answer.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {!loading && !loadError && filteredAnswers.length > 0 && totalPages > 1 && (
              <Card padding="sm" variant="outlined">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm text-muted-foreground">
                    Page {currentPage} of {totalPages}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={currentPage <= 1}
                      onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={currentPage >= totalPages}
                      onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              </Card>
            )}

            {!loading && !loadError && filteredAnswers.length === 0 && (
              <Card padding="lg" className="text-center">
                <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  {searchQuery ? 'No answers found' : 'No answers yet'}
                </h3>
                <p className="text-muted-foreground mb-6">
                  {searchQuery
                    ? 'Try a different search term'
                    : 'Start building your library of reusable answers'}
                </p>
                {!searchQuery && (
                  <Button variant="primary" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
                    <Plus className="h-4 w-4" />
                    Create Your First Answer
                  </Button>
                )}
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Categories */}
            <Card>
              <CardHeader>
                <CardTitle>Categories</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {categories.map((category) => {
                    const count = answers.filter((a) => a.category === category).length;
                    return (
                      <button
                        key={category}
                        className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-secondary transition-colors text-left"
                      >
                        <span className="text-foreground">{category}</span>
                        <span className="text-sm text-muted-foreground">{count}</span>
                      </button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Test Matcher */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-brand" />
                  <CardTitle>Test Answer Matching</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Enter a question to see which saved answer Artemis would use
                </p>
                <Input
                  placeholder="e.g., Why should we hire you?"
                  value={testQuestion}
                  onChange={(e) => setTestQuestion(e.target.value)}
                  fullWidth
                />
                <Button variant="primary" fullWidth onClick={handleTestMatch} loading={resolving}>
                  Test Match
                </Button>
                {resolutionError && (
                  <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20">
                    <p className="text-sm font-medium text-foreground mb-1">Resolution failed</p>
                    <p className="text-xs text-muted-foreground">{resolutionError}</p>
                  </div>
                )}
                {testQuestion && resolution && !resolution.needs_review && resolution.resolved_answer && (
                  <div className="p-4 rounded-lg bg-success/10 border border-success/20">
                    <p className="text-sm font-medium text-foreground mb-2">Match Found</p>
                    <p className="text-xs text-muted-foreground mb-2">
                      Source: {SOURCE_LABELS[resolution.source] || resolution.source}
                      {resolution.intent_key ? ` · Intent: ${resolution.intent_key}` : ''}
                    </p>
                    <p className="text-xs text-muted-foreground whitespace-pre-wrap break-words">
                      {resolution.resolved_answer}
                    </p>
                  </div>
                )}
                {testQuestion && resolution && (resolution.needs_review || !resolution.resolved_answer) && (
                  <div className="p-4 rounded-lg bg-warning/10 border border-warning/20">
                    <p className="text-sm font-medium text-foreground mb-1">Weak or No Match</p>
                    <p className="text-xs text-muted-foreground">
                      Artemis could not confidently resolve this question. Add a more specific reusable answer to improve matching.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Stats */}
            <Card>
              <CardHeader>
                <CardTitle>Library Stats</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Answers</span>
                    <span className="font-semibold text-foreground">{answers.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Categories</span>
                    <span className="font-semibold text-foreground">{categories.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Shown on page</span>
                    <span className="font-semibold text-foreground">
                      {paginatedAnswers.length}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
};
