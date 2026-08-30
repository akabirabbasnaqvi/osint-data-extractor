import Link from "next/link";
import { ScanEye } from "lucide-react";

export function Nav() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/80 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2.5 group">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-accent/30 bg-accent/10 text-accent transition-colors group-hover:bg-accent/20">
            <ScanEye size={17} strokeWidth={2} />
          </span>
          <span className="font-display text-[15px] font-semibold tracking-tight">
            Public<span className="text-accent">Intelligence</span>
          </span>
        </Link>

        <nav className="flex items-center gap-6 font-mono text-[13px] text-muted">
          <Link href="/history" className="transition-colors hover:text-foreground">
            history
          </Link>
          <Link
            href="/search"
            className="rounded-md border border-accent/40 bg-accent/10 px-3.5 py-1.5 text-accent transition-colors hover:bg-accent/20"
          >
            new search →
          </Link>
        </nav>
      </div>
    </header>
  );
}
