import { CheckCircle2, Loader2, XCircle, Clock } from "lucide-react";
import type { JobStatus } from "@/lib/types";

const CONFIG: Record<JobStatus, { label: string; className: string; icon: typeof Clock }> = {
  pending: { label: "queued", className: "text-muted bg-muted/10 border-border", icon: Clock },
  running: { label: "scanning", className: "text-accent bg-accent/10 border-accent/30", icon: Loader2 },
  completed: {
    label: "completed",
    className: "text-signal-high bg-signal-high/10 border-signal-high/30",
    icon: CheckCircle2,
  },
  failed: { label: "failed", className: "text-signal-low bg-signal-low/10 border-signal-low/30", icon: XCircle },
};

export function StatusBadge({ status }: { status: JobStatus }) {
  const { label, className, icon: Icon } = CONFIG[status];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 font-mono text-[11px] ${className}`}>
      <Icon size={12} className={status === "running" ? "animate-spin" : ""} />
      {label}
    </span>
  );
}
