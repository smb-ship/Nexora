"use client";

import { useEffect, useState } from "react";
import { StatusBadge } from "@/components/tickets/StatusBadge";
import { PriorityBadge } from "@/components/tickets/PriorityBadge";
import { CommentThread } from "@/components/tickets/CommentThread";
import { TicketControls } from "@/components/tickets/TicketControls";
import { getTicket, markTicketRead } from "@/lib/api/tickets";
import type { TicketDetail, TicketComment, Ticket } from "@/types/ticket";

interface InboxDetailPaneProps {
  ticketId: string | null;
  onTicketUpdated: (ticket: Ticket) => void;
}

export function InboxDetailPane({ ticketId, onTicketUpdated }: InboxDetailPaneProps) {
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!ticketId) {
      setTicket(null);
      return;
    }
    setLoading(true);
    getTicket(ticketId)
      .then((detail) => {
        setTicket(detail);
        // Mark read once opened. Separate from the GET so viewing a ticket
        // list preview elsewhere never has a side effect.
        if (detail.unread) {
          markTicketRead(ticketId).then(() => {
            const read = { ...detail, unread: false };
            setTicket(read);
            onTicketUpdated(read);
          });
        }
      })
      .finally(() => setLoading(false));
  }, [ticketId]);

  if (!ticketId) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Select a ticket to view it here.
      </div>
    );
  }

  if (loading || !ticket) {
    return <div className="p-6 text-sm text-muted-foreground">Loading…</div>;
  }

  function handleCommentAdded(comment: TicketComment) {
    setTicket((prev) => (prev ? { ...prev, comments: [...prev.comments, comment] } : prev));
  }

  function handleControlsUpdated(updated: Ticket) {
    setTicket((prev) => (prev ? { ...prev, ...updated } : prev));
    onTicketUpdated(updated);
  }

  return (
    <div className="grid h-full grid-cols-1 gap-6 overflow-y-auto p-6 lg:grid-cols-3">
      <div className="space-y-6 lg:col-span-2">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <StatusBadge status={ticket.status} />
            <PriorityBadge priority={ticket.priority} />
          </div>
          <h1 className="text-xl font-semibold">{ticket.subject}</h1>
          <p className="mt-2 text-sm text-muted-foreground">{ticket.description}</p>
        </div>
        <CommentThread ticketId={ticket.id} comments={ticket.comments} onCommentAdded={handleCommentAdded} />
      </div>
      <div>
        <TicketControls ticket={ticket} onUpdated={handleControlsUpdated} />
      </div>
    </div>
  );
}