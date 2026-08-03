"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { StatusBadge } from "@/components/tickets/StatusBadge";
import { PriorityBadge } from "@/components/tickets/PriorityBadge";
import { CommentThread } from "@/components/tickets/CommentThread";
import { TicketControls } from "@/components/tickets/TicketControls";
import { AIPanel } from "@/components/tickets/ai/AIPanel";
import { getTicket } from "@/lib/api/tickets";
import type { TicketDetail, TicketComment, Ticket } from "@/types/ticket";

export default function TicketDetailPage() {
  const params = useParams<{ id: string }>();
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [replyDraft, setReplyDraft] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getTicket(params.id)
      .then(setTicket)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load ticket"))
      .finally(() => setLoading(false));
  }, [params.id]);

  function handleCommentAdded(comment: TicketComment) {
    setTicket((prev) => (prev ? { ...prev, comments: [...prev.comments, comment] } : prev));
  }

  function handleTicketUpdated(updated: Ticket) {
    setTicket((prev) => (prev ? { ...prev, ...updated } : prev));
  }

  if (loading) return <TicketDetailSkeleton />;

  if (error || !ticket) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border py-16 text-center">
        <p className="text-sm text-foreground-muted">{error || "Ticket not found."}</p>
        <Link href="/tickets" className="text-sm text-foreground hover:underline">
          ← Back to Tickets
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      <Link href="/tickets" className="text-xs text-foreground-muted hover:underline">
        ← Back to Tickets
      </Link>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-6 lg:col-span-2">
          <div className="rounded-lg border border-border p-5">
            <div className="mb-2 flex items-center gap-2">
              <StatusBadge status={ticket.status} />
              <PriorityBadge priority={ticket.priority} />
            </div>
            <h1 className="text-xl font-semibold text-foreground tracking-tight">
              {ticket.subject}
            </h1>
            <p className="mt-2 text-sm text-foreground-muted">{ticket.description}</p>
          </div>

          <CommentThread
            ticketId={ticket.id}
            comments={ticket.comments}
            onCommentAdded={handleCommentAdded}
            draftText={replyDraft}
            onDraftConsumed={() => setReplyDraft(null)}
          />
        </div>

        <div className="flex flex-col gap-6">
          <TicketControls ticket={ticket} onUpdated={handleTicketUpdated} />
          <AIPanel ticketId={ticket.id} onUseReply={setReplyDraft} onTicketUpdated={handleTicketUpdated} />
        </div>
      </div>
    </div>
  );
}

function TicketDetailSkeleton() {
  return (
    <div className="flex animate-pulse flex-col gap-1">
      <div className="h-3 w-24 rounded bg-foreground/10" />
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-6 lg:col-span-2">
          <div className="rounded-lg border border-border p-5">
            <div className="flex gap-2">
              <div className="h-5 w-16 rounded bg-foreground/10" />
              <div className="h-5 w-16 rounded bg-foreground/10" />
            </div>
            <div className="mt-3 h-6 w-2/3 rounded bg-foreground/10" />
            <div className="mt-2 h-4 w-full rounded bg-foreground/10" />
            <div className="mt-1 h-4 w-4/5 rounded bg-foreground/10" />
          </div>
          <div className="h-40 rounded-lg border border-border" />
        </div>
        <div className="flex flex-col gap-6">
          <div className="h-32 rounded-lg border border-border" />
          <div className="h-48 rounded-lg border border-border" />
        </div>
      </div>
    </div>
  );
}