"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { analyzeSentiment } from "@/lib/api/ai";
import type { AIInsight, SentimentLabel } from "@/types/ai";

interface SectionProps {
  ticketId: string;
  insight: AIInsight | null;
  onUpdated: (insight: AIInsight) => void;
}

const SENTIMENT_STYLES: Record<SentimentLabel, string> = {
  positive: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  neutral: "border-border bg-muted text-muted-foreground",
  negative: "border-orange-500/30 bg-orange-500/10 text-orange-400",
  frustrated: "border-red-500/30 bg-red-500/10 text-red-400",
};

export function SentimentSection({ ticketId, insight, onUpdated }: SectionProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const updated = await analyzeSentiment(ticketId);
      onUpdated(updated);
    } catch {
      setError("Couldn't analyze sentiment. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-medium text-muted-foreground">Sentiment</h3>
        <Button onClick={handleGenerate} disabled={loading} className="h-7 px-2 text-xs">
          {loading ? "Analyzing…" : insight?.sentiment ? "Re-analyze" : "Analyze"}
        </Button>
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {!error && insight?.sentiment && (
        <span
          className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs capitalize ${SENTIMENT_STYLES[insight.sentiment]}`}
        >
          {insight.sentiment}
          {insight.sentiment_score !== null && (
            <span className="ml-1 opacity-70">({insight.sentiment_score.toFixed(2)})</span>
          )}
        </span>
      )}
      {!error && !loading && !insight?.sentiment && (
        <p className="text-sm text-muted-foreground">No sentiment analysis yet.</p>
      )}

      <Separator />
    </div>
  );
}