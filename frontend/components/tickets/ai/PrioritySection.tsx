"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { predictPriority } from "@/lib/api/ai";
import { updateTicket } from "@/lib/api/tickets";
import type { AIInsight } from "@/types/ai";
import type { Ticket } from "@/types/ticket";

interface SectionProps {
  ticketId: string;
  insight: AIInsight | null;
  onUpdated: (insight: AIInsight) => void;
  onTicketUpdated?: (ticket: Ticket) => void;
}

export function PrioritySection({ ticketId, insight, onUpdated, onTicketUpdated }: SectionProps) {
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const updated = await predictPriority(ticketId);
      onUpdated(updated);
    } catch {
      setError("Couldn't predict priority. Try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleApply() {
    if (!insight?.predicted_priority) return;
    setApplying(true);
    try {
      const ticket = await updateTicket(ticketId, { priority: insight.predicted_priority });
      onTicketUpdated?.(ticket);
    } finally {
      setApplying(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-medium text-muted-foreground">Priority Prediction</h3>
        <Button onClick={handleGenerate} disabled={loading} className="h-7 px-2 text-xs">
          {loading ? "Predicting…" : insight?.predicted_priority ? "Re-predict" : "Predict"}
        </Button>
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {!error && insight?.predicted_priority && (
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center rounded-full border border-border px-2 py-0.5 text-xs capitalize">
            {insight.predicted_priority}
          </span>
          {onTicketUpdated && (
            <button
              onClick={handleApply}
              disabled={applying}
              className="text-xs text-purple-400 hover:underline disabled:opacity-50"
            >
              {applying ? "Applying…" : "Apply to ticket"}
            </button>
          )}
        </div>
      )}
      {!error && !loading && !insight?.predicted_priority && (
        <p className="text-sm text-muted-foreground">No prediction yet.</p>
      )}

      <Separator />
    </div>
  );
}