import Link from "next/link";
import { ArrowRight, CheckCircle2, ScanLine, ShieldCheck, User, Zap } from "lucide-react";

const SCAN_ROWS = [
  { label: "github.com", detail: "profile, 12 repos, bio", delay: "0ms" },
  { label: "linkedin.com", detail: "headline, current role", delay: "120ms" },
  { label: "public web", detail: "2 mentions found", delay: "240ms" },
  { label: "twitter / x", detail: "handle confirmed", delay: "360ms" },
  { label: "company domain", detail: "registrant record", delay: "480ms" },
];

export default function LandingPage() {
  return (
    <main>
      {/* ---------- Hero ---------- */}
      <section className="relative overflow-hidden bg-grid bg-grid-fade bg-[length:100%_100%,40px_40px,40px_40px]">
        <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-16 px-6 pb-28 pt-20 lg:grid-cols-[1.1fr_0.9fr] lg:pt-28">
          <div className="animate-fade-up">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-muted">
              <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse-dot" />
              public data only — no logins bypassed
            </div>

            <h1 className="font-display text-[2.75rem] font-semibold leading-[1.08] tracking-tight text-foreground sm:text-6xl">
              Every public trace,
              <br />
              <span className="text-accent">one consolidated view.</span>
            </h1>

            <p className="mt-6 max-w-lg text-[17px] leading-relaxed text-muted">
              Give us a name, an email, a GitHub handle — anything. We search the open
              web and public profiles, then hand back one clean report instead of a
              dozen browser tabs.
            </p>

            <div className="mt-9 flex flex-wrap items-center gap-4">
              <Link
                href="/search"
                className="group inline-flex items-center gap-2 rounded-lg bg-accent px-5 py-3 font-medium text-accent-foreground transition-transform hover:-translate-y-0.5"
              >
                Start a search
                <ArrowRight size={16} className="transition-transform group-hover:translate-x-0.5" />
              </Link>
              <Link
                href="/history"
                className="inline-flex items-center gap-2 rounded-lg border border-border px-5 py-3 font-medium text-foreground transition-colors hover:border-border-hover hover:bg-surface"
              >
                View past searches
              </Link>
            </div>
          </div>

          {/* Decorative "live scan" panel — illustrative, not a real job */}
          <div
            className="relative animate-fade-up rounded-2xl border border-border bg-surface/80 p-5 shadow-2xl shadow-black/40 backdrop-blur"
            style={{ animationDelay: "150ms" }}
          >
            <div className="mb-4 flex items-center justify-between border-b border-border pb-4">
              <div className="flex items-center gap-2 font-mono text-xs text-muted">
                <ScanLine size={14} className="text-accent" />
                sample_scan.job
              </div>
              <span className="rounded-full bg-signal-high/10 px-2 py-0.5 font-mono text-[10px] text-signal-high">
                completed
              </span>
            </div>

            <ul className="space-y-3">
              {SCAN_ROWS.map((row) => (
                <li
                  key={row.label}
                  className="flex animate-fade-up items-center justify-between rounded-lg border border-border/60 bg-background/60 px-3.5 py-2.5"
                  style={{ animationDelay: row.delay }}
                >
                  <div className="flex items-center gap-2.5">
                    <CheckCircle2 size={15} className="shrink-0 text-signal-high" />
                    <span className="font-mono text-[13px] text-foreground">{row.label}</span>
                  </div>
                  <span className="font-mono text-[11px] text-muted-foreground">{row.detail}</span>
                </li>
              ))}
            </ul>

            <div className="pointer-events-none absolute inset-x-5 top-16 h-px overflow-hidden">
              <div className="h-24 w-full bg-gradient-to-b from-accent/0 via-accent/60 to-accent/0 animate-scan" />
            </div>
          </div>
        </div>
      </section>

      {/* ---------- How it works ---------- */}
      <section className="border-t border-border bg-surface/40 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="font-display text-2xl font-semibold tracking-tight">How it works</h2>

          <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-3">
            <Step
              index="01"
              icon={User}
              title="Tell us what you know"
              body="A name, an email, a handle — any single field is enough to start."
            />
            <Step
              index="02"
              icon={Zap}
              title="We search in parallel"
              body="GitHub, public search results, WHOIS and more are checked at once, in the background."
            />
            <Step
              index="03"
              icon={ShieldCheck}
              title="Get one clean report"
              body="Results are grouped by category with a confidence score and a source link for every entry."
            />
          </div>
        </div>
      </section>

      {/* ---------- Trust footer ---------- */}
      <footer className="border-t border-border py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-2 px-6 text-center">
          <p className="max-w-xl font-mono text-[12px] leading-relaxed text-muted-foreground">
            This tool only surfaces information that is already publicly available. It does
            not bypass logins, paywalls, or private data, and does not scrape platforms whose
            terms prohibit it.
          </p>
        </div>
      </footer>
    </main>
  );
}

function Step({
  index,
  icon: Icon,
  title,
  body,
}: {
  index: string;
  icon: typeof User;
  title: string;
  body: string;
}) {
  return (
    <div className="card-base p-6">
      <div className="mb-4 flex items-center justify-between">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-accent/30 bg-accent/10 text-accent">
          <Icon size={17} />
        </span>
        <span className="font-mono text-xs text-muted-foreground">{index}</span>
      </div>
      <h3 className="font-display text-[15px] font-semibold">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
    </div>
  );
}
