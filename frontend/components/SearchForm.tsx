"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, Search, SearchX } from "lucide-react";
import { INPUT_FIELDS, OUTPUT_CATEGORIES } from "@/lib/fields";
import type { OutputCategory, SearchInputs } from "@/lib/types";
import { submitSearch } from "@/lib/api";

// "At least one field" is enforced manually in onSubmit rather than via
// a zod .refine() — a path-less object refine doesn't map cleanly onto
// a single react-hook-form field error, and we already need custom
// placement for that message (next to the category selector, not
// under any one input) so a manual check is simpler than fighting that.
const schema = z.object({
  full_name: z.string().optional(),
  email: z.string().optional(),
  personal_email: z.string().optional(),
  city: z.string().optional(),
  country: z.string().optional(),
  linkedin: z.string().optional(),
  github: z.string().optional(),
  twitter: z.string().optional(),
  facebook: z.string().optional(),
  instagram: z.string().optional(),
  company_name: z.string().optional(),
  company_website: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

const ALL_CATEGORIES = OUTPUT_CATEGORIES.map((c) => c.key);
const GROUP_TITLES: Record<string, string> = {
  identity: "Identity",
  handles: "Social & handles",
  work: "Work",
};

export function SearchForm() {
  const router = useRouter();
  const [selected, setSelected] = useState<Set<OutputCategory>>(new Set(ALL_CATEGORIES));
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema), mode: "onSubmit" });

  const filledCount = useMemo(() => {
    const values = watch();
    return Object.values(values).filter((v) => v && String(v).trim() !== "").length;
  }, [watch()]);

  function toggleCategory(key: OutputCategory) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  async function onSubmit(values: FormValues) {
    setSubmitError(null);

    const inputs: SearchInputs = {};
    for (const [k, v] of Object.entries(values)) {
      if (v && String(v).trim() !== "") (inputs as Record<string, string>)[k] = String(v).trim();
    }

    if (Object.keys(inputs).length === 0) {
      setSubmitError("Fill in at least one field above to start a search.");
      return;
    }
    if (selected.size === 0) {
      setSubmitError("Select at least one thing to look for on the right.");
      return;
    }

    try {
      const { job_id } = await submitSearch({
        inputs,
        retrieve: Array.from(selected),
      });
      router.push(`/results/${job_id}`);
    } catch {
      setSubmitError("Couldn't reach the server. Is the backend running?");
    }
  }

  const groups = ["identity", "handles", "work"] as const;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_360px]">
      {/* ---------- Input fields ---------- */}
      <div className="space-y-6">
        {groups.map((group) => (
          <div key={group} className="card-base p-6">
            <h2 className="mb-5 font-display text-sm font-semibold text-foreground">
              {GROUP_TITLES[group]}
            </h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {INPUT_FIELDS.filter((f) => f.group === group).map((field) => {
                const Icon = field.icon;
                return (
                  <div key={field.key}>
                    <label htmlFor={field.key} className="label-base">
                      {field.label}
                    </label>
                    <div className="relative">
                      <Icon size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                      <input
                        id={field.key}
                        placeholder={field.placeholder}
                        className="input-base pl-9"
                        {...register(field.key)}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* ---------- Output selector + submit (sticky) ---------- */}
      <div className="lg:sticky lg:top-24 lg:self-start">
        <div className="card-base p-6">
          <h2 className="mb-1 font-display text-sm font-semibold text-foreground">
            What are you looking for?
          </h2>
          <p className="mb-5 text-xs text-muted">All selected by default — untick what you don't need.</p>

          <div className="flex flex-wrap gap-2">
            {OUTPUT_CATEGORIES.map((cat) => {
              const active = selected.has(cat.key);
              const Icon = cat.icon;
              return (
                <button
                  type="button"
                  key={cat.key}
                  onClick={() => toggleCategory(cat.key)}
                  className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[13px] transition-colors ${
                    active
                      ? "border-accent/50 bg-accent/15 text-accent"
                      : "border-border text-muted hover:border-border-hover hover:text-foreground"
                  }`}
                >
                  <Icon size={13} />
                  {cat.label}
                </button>
              );
            })}
          </div>

          <div className="mt-6 flex items-center justify-between border-t border-border pt-5">
            <span className="font-mono text-[11px] text-muted-foreground">
              {filledCount} field{filledCount === 1 ? "" : "s"} filled
            </span>
            <span className="font-mono text-[11px] text-muted-foreground">
              {selected.size} categor{selected.size === 1 ? "y" : "ies"}
            </span>
          </div>

          {submitError && (
            <p className="mt-4 flex items-center gap-1.5 text-[13px] text-signal-low">
              <SearchX size={14} /> {submitError}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg bg-accent py-3 font-medium text-accent-foreground transition-transform hover:-translate-y-0.5 disabled:opacity-60 disabled:hover:translate-y-0"
          >
            {isSubmitting ? (
              <>
                <Loader2 size={16} className="animate-spin" /> Starting search…
              </>
            ) : (
              <>
                <Search size={16} /> Run search
              </>
            )}
          </button>
        </div>
      </div>
    </form>
  );
}
