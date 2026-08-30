import { ExternalLink } from "lucide-react";
import type { OutputCategoryDef } from "@/lib/fields";
import type { ResultEntry } from "@/lib/types";

function confidenceClass(score: number): string {
  if (score >= 0.8) return "text-signal-high bg-signal-high/10 border-signal-high/30";
  if (score >= 0.5) return "text-signal-medium bg-signal-medium/10 border-signal-medium/30";
  return "text-signal-low bg-signal-low/10 border-signal-low/30";
}

function confidenceLabel(score: number): string {
  if (score >= 0.8) return "high";
  if (score >= 0.5) return "medium";
  return "low";
}

function timeAgo(iso: string): string {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000));
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

function formatDataValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "yes" : "no";
  return String(value);
}

export function ResultCard({ category, entries }: { category: OutputCategoryDef; entries: ResultEntry[] }) {
  const Icon = category.icon;

  return (
    <div className="card-base animate-fade-up overflow-hidden">
      <div className="flex items-center gap-2.5 border-b border-border bg-surface-raised/60 px-5 py-3.5">
        <span className="flex h-7 w-7 items-center justify-center rounded-md border border-accent/30 bg-accent/10 text-accent">
          <Icon size={14} />
        </span>
        <h3 className="font-display text-[14px] font-semibold">{category.label}</h3>
        <span className="ml-auto font-mono text-[11px] text-muted-foreground">
          {entries.length} {entries.length === 1 ? "match" : "matches"}
        </span>
      </div>

      <ul className="divide-y divide-border">
        {entries.map((entry, i) => (
          <li key={i} className="px-5 py-4">
            <div className="mb-2 flex items-start justify-between gap-3">
              <div className="min-w-0 space-y-1">
                {Object.entries(entry.data)
                  .filter(([, v]) => v !== null && v !== undefined && v !== "")
                  .slice(0, 6)
                  .map(([key, value]) => (
                    <div key={key} className="flex gap-2 text-[13px]">
                      <span className="shrink-0 font-mono text-[11px] uppercase tracking-wide text-muted-foreground">
                        {key.replace(/_/g, " ")}
                      </span>
                      <span className="truncate text-foreground">{formatDataValue(value)}</span>
                    </div>
                  ))}
              </div>
              <span
                className={`shrink-0 rounded-full border px-2 py-0.5 font-mono text-[10px] ${confidenceClass(
                  entry.confidence
                )}`}
              >
                {confidenceLabel(entry.confidence)}
              </span>
            </div>

            <div className="flex items-center justify-between text-[11px] text-muted-foreground">
              <span className="font-mono">{timeAgo(entry.scraped_at)}</span>
              {entry.source_url && (
                <a
                  href={entry.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-accent hover:underline"
                >
                  source <ExternalLink size={11} />
                </a>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
