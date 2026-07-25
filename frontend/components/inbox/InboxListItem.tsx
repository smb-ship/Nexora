"use client";

import { cn } from "@/lib/utils";
import { PriorityBadge } from "@/components/tickets/PriorityBadge";
import { formatRelativeTime } from "@/lib/format-relative-time";
import type { Ticket } from "@/types/ticket";

interface InboxListItemProps {
  ticket: Ticket;
  active: boolean;
  onClick: () => void;
}

export function InboxListItem({ ticket, active, onClick }: InboxListItemProps) {
  return (
    <button
      data-slot="inbox-list-item"
      onClick={onClick}
      className={cn(
        "flex w-full flex-col gap-1 border-b border-border px-3 py-2.5 text-left transition-colors",
        active ? "bg-accent" : "hover:bg-muted/50"
      )}
    >
      <div className="flex items-center gap-2">
        {ticket.unread && (
          <span className="size-1.5 shrink-0 rounded-full bg-primary" aria-label="Unread" />
        )}
        <span
          className={cn(
            "flex-1 truncate text-sm",
            ticket.unread ? "font-semibold text-foreground" : "font-medium text-foreground/90"
          )}
        >
          {ticket.subject}
        </span>
        <span className="shrink-0 text-xs text-muted-foreground">
          {formatRelativeTime(ticket.updated_at)}
        </span>
      </div>
      <div className="flex items-center justify-between pl-3.5">
        <span className="truncate text-xs text-muted-foreground">{ticket.requester_name}</span>
        <PriorityBadge priority={ticket.priority} />
      </div>
    </button>
  );
}