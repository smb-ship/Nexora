"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { summarizeTicket } from "@/lib/api/ai";
import type { AIInsight } from "@/types/ai";

interface SectionProps {
  ticketId: string;
  insight: AIInsight | null;
  onUpdated: (insight: AIInsight) => void;
}

export function SummarySection({ ticketId, insight, onUpdated }: SectionProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const updated = await summarizeTicket(ticketId);
      onUpdated(updated);
    } catch {
      setError("Couldn't generate a summary. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-medium text-muted-foreground">Summary</h3>
        <Button onClick={handleGenerate} disabled={loading} className="h-7 px-2 text-xs">
          {loading ? "Summarizing…" : insight?.summary ? "Regenerate" : "Generate"}
        </Button>
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {!error && insight?.summary && <p className="text-sm">{insight.summary}</p>}
      {!error && !loading && !insight?.summary && (
        <p className="text-sm text-muted-foreground">No summary yet.</p>
      )}

      <Separator />
    </div>
  );
}