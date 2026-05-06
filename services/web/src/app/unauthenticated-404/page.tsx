// Purpose: Render a modern 404-style page for unauthenticated users.
import Link from "next/link";
import { ArrowLeft, SearchX } from "lucide-react";

import { buttonVariants } from "../components/ui/button";
import { cn } from "../components/ui/utils";

export default function UnauthenticatedNotFoundPage() {
  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-6 py-16 text-foreground">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_right,var(--color-brand-light),transparent_40%),radial-gradient(circle_at_bottom_left,var(--color-secondary),transparent_35%)]" />

      <section className="w-full max-w-xl rounded-2xl border border-border bg-card/95 p-8 shadow-sm backdrop-blur sm:p-10">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-brand-light px-3 py-1 text-xs font-medium text-brand-dark">
          <SearchX className="h-4 w-4" />
          Page Not Found
        </div>

        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          This page isn&apos;t available.
        </h1>
        <p className="mt-3 text-sm text-muted-foreground sm:text-base">
          It may have been moved, removed, or you may need an account to continue.
        </p>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <Link href="/" className={cn(buttonVariants({ variant: "default", size: "lg" }), "sm:min-w-44")}>
            <ArrowLeft className="h-4 w-4" />
            Back Home
          </Link>
        </div>
      </section>
    </main>
  );
}
