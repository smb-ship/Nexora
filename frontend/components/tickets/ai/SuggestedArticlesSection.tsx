"use client";

import { useEffect, useState } from "react";
import { BookOpen } from "lucide-react";
import { suggestArticlesForTicket, type SuggestedArticle } from "@/services/knowledge";

export function SuggestedArticlesSection({ ticketId }: { ticketId: string }) {
  const [articles, setArticles] = useState<SuggestedArticle[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    suggestArticlesForTicket(ticketId)
      .then((data) => { if (!cancelled) setArticles(data); })
      .catch(() => { if (!cancelled) setError("Couldn't load suggestions."); });
    return () => { cancelled = true; };
  }, [ticketId]);

  return (
    <div className="border-t border-border pt-4">
      <div className="flex items-center gap-2">
        <BookOpen className="h-4 w-4 text-foreground-muted" />
        <h3 className="text-xs font-semibold text-foreground">Suggested Articles</h3>
      </div>
      {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
      {articles === null && !error && <p className="mt-2 text-xs text-foreground-muted">Loading...</p>}
      {articles?.length === 0 && <p className="mt-2 text-xs text-foreground-muted">No relevant articles found.</p>}
      <div className="mt-2 flex flex-col gap-2">
        {articles?.map((a) => (
          <a key={a.id} href={`/knowledge/${a.id}`} className="rounded-md border border-border p-2 text-xs hover:bg-foreground/5">
            <p className="font-medium text-foreground">{a.title}</p>
            <p className="mt-0.5 text-foreground-subtle">{a.reason}</p>
          </a>
        ))}
      </div>
    </div>
  );
}