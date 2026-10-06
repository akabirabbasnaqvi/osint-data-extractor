/**
 * Returns the URL only if it is a plain http(s) link, otherwise null.
 *
 * Result URLs originate from third-party search results, so they must never
 * be put into an `href` unchecked: `javascript:` and `data:` links run script
 * in this app's origin when clicked.
 */
export function safeHttpUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:" ? url.href : null;
  } catch {
    return null;
  }
}
