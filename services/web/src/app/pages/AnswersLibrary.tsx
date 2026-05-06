import React, { useState } from 'react';
import { AppShell } from '../components/AppShell';
import { Button, Card, CardHeader, CardTitle, CardContent, Input } from '../components/ui';
import { Plus, Search, Edit, Trash2, BookOpen, Sparkles } from 'lucide-react';

interface SavedAnswer {
  id: string;
  question: string;
  answer: string;
  category: string;
  lastUsed?: string;
  timesUsed: number;
}

const mockAnswers: SavedAnswer[] = [
  {
    id: '1',
    question: 'Why do you want to work here?',
    answer: "I am passionate about building products that solve real problems for users. Your company's mission to transform team collaboration aligns perfectly with my experience in SaaS product management. I've followed your journey since the Series A and am impressed by how you've maintained product quality while scaling rapidly.",
    category: 'Motivation',
    lastUsed: '2 days ago',
    timesUsed: 5,
  },
  {
    id: '2',
    question: 'Describe your product management experience',
    answer: "Over the past 5 years, I have led cross-functional teams to ship products that drive business growth. At my current role, I own the product roadmap for a B2B SaaS platform serving 10,000+ customers. I've successfully launched features that increased user engagement by 40% and reduced churn by 25%. My approach combines data-driven decision-making with deep user empathy.",
    category: 'Experience',
    lastUsed: '1 week ago',
    timesUsed: 8,
  },
  {
    id: '3',
    question: 'What is your biggest professional achievement?',
    answer: 'I successfully launched a SaaS platform that grew from 0 to $10M ARR in 18 months. This involved defining the product vision, building a cross-functional team, establishing product-market fit, and scaling operations. The experience taught me how to balance speed with quality and how to make difficult prioritization decisions under pressure.',
    category: 'Achievements',
    lastUsed: '3 days ago',
    timesUsed: 12,
  },
  {
    id: '4',
    question: 'How do you handle conflict with stakeholders?',
    answer: "I believe conflicts often stem from misaligned expectations or incomplete information. My approach is to first listen deeply to understand the stakeholder's perspective and constraints. Then I share data and user insights to establish a common understanding. Finally, I work collaboratively to find solutions that balance business needs with user value. Transparency and empathy are key.",
    category: 'Teamwork',
    timesUsed: 3,
  },
];

export const AnswersLibrary: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [testQuestion, setTestQuestion] = useState('');
  const [matchedAnswer, setMatchedAnswer] = useState<SavedAnswer | null>(null);

  const filteredAnswers = mockAnswers.filter(
    (answer) =>
      answer.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      answer.answer.toLowerCase().includes(searchQuery.toLowerCase()) ||
      answer.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleTestMatch = () => {
    const match = mockAnswers.find(
      (answer) => answer.question.toLowerCase().includes(testQuestion.toLowerCase())
    );
    setMatchedAnswer(match || null);
  };

  const handleCreateAnswer = () => {
    // In a real app, this would open a modal or navigate to a form
    alert('Create new answer functionality would be implemented here');
  };

  const handleEditAnswer = (id: string) => {
    alert(`Edit answer ${id}`);
  };

  const handleDeleteAnswer = (id: string) => {
    alert(`Delete answer ${id}`);
  };

  const categories = Array.from(new Set(mockAnswers.map((a) => a.category)));

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-semibold text-foreground">Answers Library</h1>
              <p className="mt-2 text-muted-foreground">
                Build a reusable knowledge base of your best application answers
              </p>
            </div>
            <Button variant="primary" onClick={handleCreateAnswer}>
              <Plus className="h-4 w-4" />
              New Answer
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

            {/* Answers List */}
            <div className="space-y-4">
              {filteredAnswers.map((answer) => (
                <Card key={answer.id} padding="md" variant="outlined">
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex items-start gap-3 flex-1">
                      <BookOpen className="h-5 w-5 text-brand flex-shrink-0 mt-1" />
                      <div className="flex-1">
                        <h3 className="font-semibold text-foreground mb-1">{answer.question}</h3>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-xs px-2 py-1 rounded-full bg-brand/10 text-brand font-medium">
                            {answer.category}
                          </span>
                          {answer.lastUsed && (
                            <span className="text-xs text-muted-foreground">
                              Last used {answer.lastUsed}
                            </span>
                          )}
                          <span className="text-xs text-muted-foreground">
                            Used {answer.timesUsed} times
                          </span>
                        </div>
                        <p className="text-muted-foreground leading-relaxed">{answer.answer}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEditAnswer(answer.id)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteAnswer(answer.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {filteredAnswers.length === 0 && (
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
                  <Button variant="primary" onClick={handleCreateAnswer}>
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
                    const count = mockAnswers.filter((a) => a.category === category).length;
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
                <Button variant="primary" fullWidth onClick={handleTestMatch}>
                  Test Match
                </Button>
                {testQuestion && matchedAnswer && (
                  <div className="p-4 rounded-lg bg-success/10 border border-success/20">
                    <p className="text-sm font-medium text-foreground mb-2">Match Found</p>
                    <p className="text-sm text-muted-foreground mb-2">{matchedAnswer.question}</p>
                    <p className="text-xs text-muted-foreground line-clamp-3">{matchedAnswer.answer}</p>
                  </div>
                )}
                {testQuestion && !matchedAnswer && (
                  <div className="p-4 rounded-lg bg-warning/10 border border-warning/20">
                    <p className="text-sm font-medium text-foreground mb-1">No Match Found</p>
                    <p className="text-xs text-muted-foreground">
                      Consider creating a new answer for this question
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
                    <span className="font-semibold text-foreground">{mockAnswers.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Categories</span>
                    <span className="font-semibold text-foreground">{categories.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Avg. Uses</span>
                    <span className="font-semibold text-foreground">
                      {Math.round(mockAnswers.reduce((sum, a) => sum + a.timesUsed, 0) / mockAnswers.length)}
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
