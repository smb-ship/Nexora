"use client";

import { InboxListItem } from "./InboxListItem";
import type { Ticket } from "@/types/ticket";

interface InboxListProps {
  tickets: Ticket[];
  selectedId: string | null;
  loading: boolean;
  onSelect: (ticket: Ticket) => void;
}

export function InboxList({ tickets, selectedId, loading, onSelect }: InboxListProps) {
  if (loading) {
    return <div className="p-4 text-sm text-muted-foreground">Loading…</div>;
  }

  if (tickets.length === 0) {
    return <div className="p-4 text-sm text-muted-foreground">No tickets here.</div>;
  }

  return (
    <div data-slot="inbox-list" className="flex flex-col overflow-y-auto">
      {tickets.map((ticket) => (
        <InboxListItem
          key={ticket.id}
          ticket={ticket}
          active={ticket.id === selectedId}
          onClick={() => onSelect(ticket)}
        />
      ))}
    </div>
  );
}