"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Inbox, Trash2 } from "lucide-react";
import { deleteJob, listJobs } from "@/lib/api";
import type { JobSummary } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";

function summarize(inputs: JobSummary["inputs"]): string {
  const parts = [inputs.full_name, inputs.email, inputs.github, inputs.linkedin].filter(Boolean);
  return parts.length > 0 ? parts.join(" · ") : "no identifying fields";
}

export default function HistoryPage() {
  const [jobs, setJobs] = useState<JobSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listJobs()
      .then(setJobs)
      .catch((err) => setError(err instanceof Error ? err.message : "Couldn't load your searches."));
  }, []);

  async function handleDelete(jobId: string) {
    if (!window.confirm("Delete this search and its results? This cannot be undone.")) return;
    try {
      await deleteJob(jobId);
      setJobs((current) => current?.filter((job) => job.job_id !== jobId) ?? null);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't delete that search.");
    }
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-14">
      <p className="font-mono text-[11px] uppercase tracking-wider text-accent">history</p>
      <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight">Past searches</h1>

      {error && <p className="mt-6 text-sm text-signal-low">{error}</p>}

      {jobs && jobs.length === 0 && (
        <div className="mt-10 flex flex-col items-center gap-3 rounded-lg border border-border bg-surface px-5 py-14 text-center">
          <Inbox size={22} className="text-muted-foreground" />
          <p className="text-sm text-muted">No searches yet.</p>
          <Link href="/search" className="text-sm text-accent hover:underline">
            Run your first search →
          </Link>
        </div>
      )}

      <ul className="mt-8 divide-y divide-border overflow-hidden rounded-xl border border-border">
        {jobs?.map((job) => (
          <li key={job.job_id} className="flex items-stretch bg-surface transition-colors hover:bg-surface-raised">
            <Link
              href={`/results/${job.job_id}`}
              className="group flex min-w-0 flex-1 items-center justify-between gap-4 py-4 pl-5 pr-3"
            >
              <div className="min-w-0">
                <p className="truncate text-sm text-foreground">{summarize(job.inputs)}</p>
                <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                  {new Date(job.created_at).toLocaleString()}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <StatusBadge status={job.status} />
                <ArrowRight size={14} className="text-muted-foreground transition-transform group-hover:translate-x-0.5" />
              </div>
            </Link>
            <button
              type="button"
              onClick={() => handleDelete(job.job_id)}
              aria-label="Delete this search"
              title="Delete this search"
              className="px-4 text-muted-foreground transition-colors hover:text-signal-low"
            >
              <Trash2 size={15} />
            </button>
          </li>
        ))}
      </ul>
    </main>
  );
}
