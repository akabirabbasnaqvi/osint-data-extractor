import { SearchForm } from "@/components/SearchForm";

export default function SearchPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-14">
      <div className="mb-10">
        <p className="font-mono text-[11px] uppercase tracking-wider text-accent">new search</p>
        <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight">
          What do you know about them?
        </h1>
        <p className="mt-2 max-w-xl text-sm text-muted">
          Any single field below is enough — the more you give us, the more precisely we
          can cross-reference results.
        </p>
      </div>

      <SearchForm />
    </main>
  );
}
