"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AlertTriangle, ArrowLeft, Download } from "lucide-react";
import { getResults } from "@/lib/api";
import { OUTPUT_CATEGORIES } from "@/lib/fields";
import type { JobStatusResponse } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";
import { ResultCard } from "@/components/ResultCard";

const POLL_INTERVAL_MS = 2500;

export default function ResultsPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    async function poll() {
      try {
        const data = await getResults(jobId);
        if (cancelled) return;
        setJob(data);
        setError(null);
        if (data.status === "pending" || data.status === "running") {
          timer = setTimeout(poll, POLL_INTERVAL_MS);
        }
      } catch {
        if (!cancelled) setError("Couldn't reach the server. Is the backend running?");
      }
    }

    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [jobId]);

  function downloadJson() {
    if (!job) return;
    const blob = new Blob([JSON.stringify(job, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `search-${job.job_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const categoriesWithResults = OUTPUT_CATEGORIES.filter((c) => (job?.results[c.key]?.length ?? 0) > 0);
  const isActive = job?.status === "pending" || job?.status === "running";

  return (
    <main className="mx-auto max-w-4xl px-6 py-14">
      <Link href="/search" className="mb-8 inline-flex items-center gap-1.5 text-sm text-muted hover:text-foreground">
        <ArrowLeft size={14} /> New search
      </Link>

      <div className="mb-8 flex flex-wrap items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <p className="font-mono text-[11px] text-muted-foreground">job / {jobId}</p>
          <h1 className="mt-1 font-display text-2xl font-semibold tracking-tight">Search results</h1>
        </div>
        <div className="flex items-center gap-3">
          {job && <StatusBadge status={job.status} />}
          {job?.status === "completed" && (
            <button
              onClick={downloadJson}
              className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-[13px] text-muted transition-colors hover:border-border-hover hover:text-foreground"
            >
              <Download size={13} /> export JSON
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-6 flex items-center gap-2 rounded-lg border border-signal-low/30 bg-signal-low/10 px-4 py-3 text-sm text-signal-low">
          <AlertTriangle size={15} /> {error}
        </div>
      )}

      {isActive && (
        <div className="mb-8 flex items-center gap-3 rounded-lg border border-accent/20 bg-accent/5 px-4 py-3.5">
          <span className="h-2 w-2 shrink-0 animate-pulse-dot rounded-full bg-accent" />
          <p className="text-[13px] text-muted">
            Searching public sources — results below will appear as each one finishes.
          </p>
        </div>
      )}

      {job?.status === "failed" && (
        <div className="mb-8 rounded-lg border border-signal-low/30 bg-signal-low/10 px-4 py-3.5 text-[13px] text-signal-low">
          {job.error_msg || "This search failed. Try again."}
        </div>
      )}

      {job && categoriesWithResults.length === 0 && !isActive && (
        <div className="rounded-lg border border-border bg-surface px-5 py-8 text-center text-sm text-muted">
          No public matches were found for the details you provided.
        </div>
      )}

      <div className="space-y-5">
        {categoriesWithResults.map((cat) => (
          <ResultCard key={cat.key} category={cat} entries={job!.results[cat.key]!} />
        ))}
      </div>
    </main>
  );
}
