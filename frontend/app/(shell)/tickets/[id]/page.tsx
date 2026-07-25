"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
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
  const [replyDraft, setReplyDraft] = useState<string | null>(null);

  useEffect(() => {
    getTicket(params.id).then(setTicket).finally(() => setLoading(false));
  }, [params.id]);

  if (loading) return <div className="p-6 text-muted-foreground">Loading…</div>;
  if (!ticket) return <div className="p-6 text-muted-foreground">Ticket not found.</div>;

  function handleCommentAdded(comment: TicketComment) {
    setTicket((prev) => (prev ? { ...prev, comments: [...prev.comments, comment] } : prev));
  }

  function handleTicketUpdated(updated: Ticket) {
    setTicket((prev) => (prev ? { ...prev, ...updated } : prev));
  }

  return (
    <div className="grid grid-cols-1 gap-6 p-6 lg:grid-cols-3">
      <div className="space-y-6 lg:col-span-2">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <StatusBadge status={ticket.status} />
            <PriorityBadge priority={ticket.priority} />
          </div>
          <h1 className="text-2xl font-semibold">{ticket.subject}</h1>
          <p className="mt-2 text-muted-foreground">{ticket.description}</p>
        </div>

        <CommentThread
          ticketId={ticket.id}
          comments={ticket.comments}
          onCommentAdded={handleCommentAdded}
          draftText={replyDraft}
          onDraftConsumed={() => setReplyDraft(null)}
        />
      </div>

      <div className="space-y-6">
        <TicketControls ticket={ticket} onUpdated={handleTicketUpdated} />
        <AIPanel ticketId={ticket.id} onUseReply={setReplyDraft} onTicketUpdated={handleTicketUpdated} />
      </div>
    </div>
  );
}