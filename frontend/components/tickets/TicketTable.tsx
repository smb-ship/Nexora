"use client";

import { useRouter } from "next/navigation";
import { StatusBadge } from "./StatusBadge";
import { PriorityBadge } from "./PriorityBadge";
import { ChannelBadge } from "./ChannelBadge";
import type { Ticket } from "@/types/ticket";

export function TicketTable({ tickets }: { tickets: Ticket[] }) {
  const router = useRouter();

  if (tickets.length === 0) {
    return (
      <div className="rounded-lg border border-border p-10 text-center text-muted-foreground">
        No tickets match the current filters.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-left text-muted-foreground">
          <tr>
            <th className="px-4 py-3 font-medium">Subject</th>
            <th className="px-4 py-3 font-medium">Requester</th>
            <th className="px-4 py-3 font-medium">Channel</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Priority</th>
            <th className="px-4 py-3 font-medium">Updated</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((ticket) => (
            <tr
              key={ticket.id}
              onClick={() => router.push(`/tickets/${ticket.id}`)}
              className={`cursor-pointer border-t border-border hover:bg-muted/30 ${
                ticket.unread ? "font-semibold" : ""
              }`}
            >
              <td className="px-4 py-3">{ticket.subject}</td>
              <td className="px-4 py-3 text-muted-foreground font-normal">{ticket.requester_name}</td>
              <td className="px-4 py-3"><ChannelBadge source={ticket.source} /></td>
              <td className="px-4 py-3"><StatusBadge status={ticket.status} /></td>
              <td className="px-4 py-3"><PriorityBadge priority={ticket.priority} /></td>
              <td className="px-4 py-3 text-muted-foreground font-normal">
                {new Date(ticket.updated_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}