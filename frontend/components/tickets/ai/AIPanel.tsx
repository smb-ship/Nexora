"use client";

import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { getAIInsights } from "@/lib/api/ai";
import type { AIInsight } from "@/types/ai";
import type { Ticket } from "@/types/ticket";
import { SummarySection } from "@/components/tickets/ai/SummarySection";
import { SentimentSection } from "@/components/tickets/ai/SentimentSection";
import { PrioritySection } from "@/components/tickets/ai/PrioritySection";
import { TagsSection } from "@/components/tickets/ai/TagsSection";
import { ReplySuggestionSection } from "@/components/tickets/ai/ReplySuggestionSection";
import { InternalNoteSection } from "@/components/tickets/ai/InternalNoteSection";
import { SuggestedArticlesSection } from "@/components/tickets/ai/SuggestedArticlesSection";

interface AIPanelProps {
  ticketId: string;
  onUseReply?: (text: string) => void;
  onTicketUpdated?: (ticket: Ticket) => void;
}

export function AIPanel({ ticketId, onUseReply, onTicketUpdated }: AIPanelProps) {
  const [insight, setInsight] = useState<AIInsight | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError(null);
    getAIInsights(ticketId)
      .then((data) => {
        if (!cancelled) setInsight(data);
      })
      .catch(() => {
        if (!cancelled) setLoadError("Couldn't load AI insights.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [ticketId]);

  return (
    <div className="space-y-4 rounded-lg border border-border p-4">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-purple-400" />
        <h2 className="text-sm font-semibold">AI Workspace</h2>
      </div>

      {loading && <p className="text-sm text-muted-foreground">Loading AI insights…</p>}
      {!loading && loadError && <p className="text-sm text-red-400">{loadError}</p>}

      {!loading && !loadError && (
        <div className="space-y-4">
          <SummarySection ticketId={ticketId} insight={insight} onUpdated={setInsight} />
          <SentimentSection ticketId={ticketId} insight={insight} onUpdated={setInsight} />
          <PrioritySection
            ticketId={ticketId}
            insight={insight}
            onUpdated={setInsight}
            onTicketUpdated={onTicketUpdated}
          />
          <TagsSection ticketId={ticketId} insight={insight} onUpdated={setInsight} />
          <ReplySuggestionSection ticketId={ticketId} onUseReply={onUseReply} />
          <InternalNoteSection ticketId={ticketId} insight={insight} onUpdated={setInsight} />
          <SuggestedArticlesSection ticketId={ticketId} />
        </div>
      )}
    </div>
  );
}