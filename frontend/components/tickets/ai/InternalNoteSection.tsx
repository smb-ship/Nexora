"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Lock } from "lucide-react";
import { generateInternalNote } from "@/lib/api/ai";
import type { AIInsight } from "@/types/ai";

interface SectionProps {
  ticketId: string;
  insight: AIInsight | null;
  onUpdated: (insight: AIInsight) => void;
}

export function InternalNoteSection({ ticketId, insight, onUpdated }: SectionProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const updated = await generateInternalNote(ticketId);
      onUpdated(updated);
    } catch {
      setError("Couldn't generate an internal note. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-1 text-xs font-medium text-muted-foreground">
          <Lock className="h-3 w-3" />
          Internal AI Notes
        </h3>
        <Button onClick={handleGenerate} disabled={loading} className="h-7 px-2 text-xs">
          {loading ? "Generating…" : insight?.internal_ai_notes ? "Regenerate" : "Generate"}
        </Button>
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {!error && insight?.internal_ai_notes && (
        <p className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-100">
          {insight.internal_ai_notes}
        </p>
      )}
      {!error && !loading && !insight?.internal_ai_notes && (
        <p className="text-sm text-muted-foreground">No internal notes yet.</p>
      )}
    </div>
  );
}