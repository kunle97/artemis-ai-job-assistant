"use client";

import React, { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Sparkles, Briefcase, FileText, BookOpen, User, Settings, Search, Menu, X, SlidersHorizontal } from 'lucide-react';
import { FollowUpDropdown } from './FollowUpDropdown';
import {
  clearStoredTokens,
  getCurrentSession,
  getStoredAccessToken,
  getStoredRefreshToken,
  logoutUser,
  type SessionUser,
} from '../../services/auth/auth.service';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sessionUser, setSessionUser] = useState<SessionUser | null>(null);
  const pathname = usePathname();
  const router = useRouter();

  const navigation = [
    { name: 'Job Feed', href: '/jobs', icon: Search },
    { name: 'Applications', href: '/applications', icon: Briefcase },
    { name: 'Answers Library', href: '/answers', icon: BookOpen },
    { name: 'Resumes', href: '/resumes', icon: FileText },
  ];

  const secondaryNavigation = [
    { name: 'Candidate Profile', href: '/profile', icon: User },
    { name: 'Job Preferences', href: '/job-preferences', icon: SlidersHorizontal },
    { name: 'My Account', href: '/account', icon: Settings },
  ];

  const handleNavigate = (href: string) => {
    router.push(href);
  };

  const handleSignOut = async () => {
    const accessToken = getStoredAccessToken();
    const refreshToken = getStoredRefreshToken();

    try {
      if (accessToken) {
        await logoutUser(accessToken, refreshToken ?? undefined);
      }
    } finally {
      clearStoredTokens();
      router.push('/signin');
    }
  };

  useEffect(() => {
    const loadSessionUser = async () => {
      const accessToken = getStoredAccessToken();
      if (!accessToken) {
        setSessionUser(null);
        return;
      }

      try {
        const user = await getCurrentSession(accessToken);
        setSessionUser(user);
      } catch {
        // Non-blocking: keep shell usable even if session lookup fails.
        setSessionUser(null);
      }
    };

    void loadSessionUser();
  }, []);

  const fullName = [sessionUser?.first_name, sessionUser?.last_name]
    .map((part) => (part || '').trim())
    .filter((part) => part.length > 0)
    .join(' ');

  const displayName = fullName || sessionUser?.email || 'Account';
  const displayEmail = sessionUser?.email || '';
  const initials = fullName
    ? fullName
      .split(' ')
      .filter((part) => part.length > 0)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() || '')
      .join('')
    : (sessionUser?.email?.charAt(0).toUpperCase() || 'A');

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-foreground/20 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border transform transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center gap-2 px-6 border-b border-border">
            <Sparkles className="h-8 w-8 text-brand" />
            <span className="text-xl font-semibold text-foreground">Artemis</span>
            <button onClick={() => setSidebarOpen(false)} className="ml-auto lg:hidden">
              <X className="h-6 w-6 text-muted-foreground" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
              return (
                <button
                  key={item.name}
                  onClick={() => handleNavigate(item.href)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-brand text-brand-foreground'
                      : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  {item.name}
                </button>
              );
            })}

            <div className="pt-4 mt-4 border-t border-border">
              {secondaryNavigation.map((item) => {
                const Icon = item.icon;
                const isActive =
                  pathname === item.href ||
                  (item.href !== '/profile' && pathname.startsWith(item.href + '/'));
                return (
                  <button
                    key={item.name}
                    onClick={() => handleNavigate(item.href)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-brand text-brand-foreground'
                        : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    {item.name}
                  </button>
                );
              })}
            </div>
          </nav>

          {/* User section */}
          <div className="border-t border-border p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="h-10 w-10 rounded-full bg-brand text-brand-foreground flex items-center justify-center font-semibold">
                {initials}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{displayName}</p>
                <p className="text-xs text-muted-foreground truncate">{displayEmail}</p>
              </div>
            </div>
            <button
              onClick={handleSignOut}
              className="w-full text-sm text-muted-foreground hover:text-foreground text-left"
            >
              Sign out
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-background/95 backdrop-blur px-6">
          <button onClick={() => setSidebarOpen(true)} className="lg:hidden">
            <Menu className="h-6 w-6 text-muted-foreground" />
          </button>
          <div className="flex-1" />
          <FollowUpDropdown />
        </header>

        {/* Page content */}
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
};
