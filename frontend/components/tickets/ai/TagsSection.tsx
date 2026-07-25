"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { suggestTags } from "@/lib/api/ai";
import type { AIInsight } from "@/types/ai";

interface SectionProps {
  ticketId: string;
  insight: AIInsight | null;
  onUpdated: (insight: AIInsight) => void;
}

export function TagsSection({ ticketId, insight, onUpdated }: SectionProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const updated = await suggestTags(ticketId);
      onUpdated(updated);
    } catch {
      setError("Couldn't suggest tags. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-medium text-muted-foreground">Suggested Tags</h3>
        <Button onClick={handleGenerate} disabled={loading} className="h-7 px-2 text-xs">
          {loading ? "Tagging…" : insight?.suggested_tags?.length ? "Regenerate" : "Suggest"}
        </Button>
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {!error && insight?.suggested_tags && insight.suggested_tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {insight.suggested_tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center rounded-full border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 text-xs text-purple-300"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
      {!error && !loading && !insight?.suggested_tags?.length && (
        <p className="text-sm text-muted-foreground">No tags suggested yet.</p>
      )}

      <Separator />
    </div>
  );
}