"use client";

import { useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { updateTicket } from "@/lib/api/tickets";
import type { Ticket, TicketStatus, TicketPriority } from "@/types/ticket";

export function TicketControls({ ticket, onUpdated }: { ticket: Ticket; onUpdated: (t: Ticket) => void }) {
  const [saving, setSaving] = useState(false);

  async function handleStatusChange(status: TicketStatus) {
    setSaving(true);
    try {
      const updated = await updateTicket(ticket.id, { status });
      onUpdated(updated);
    } finally {
      setSaving(false);
    }
  }

  async function handlePriorityChange(priority: TicketPriority) {
    setSaving(true);
    try {
      const updated = await updateTicket(ticket.id, { priority });
      onUpdated(updated);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4 rounded-lg border border-border p-4">
      <div>
        <label className="mb-1 block text-xs font-medium text-muted-foreground">Status</label>
        <Select value={ticket.status} onValueChange={(v) => handleStatusChange(v as TicketStatus)} disabled={saving}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="open">Open</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="on_hold">On Hold</SelectItem>
            <SelectItem value="resolved">Resolved</SelectItem>
            <SelectItem value="closed">Closed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-muted-foreground">Priority</label>
        <Select value={ticket.priority} onValueChange={(v) => handlePriorityChange(v as TicketPriority)} disabled={saving}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="low">Low</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="urgent">Urgent</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="border-t border-border pt-3 text-xs text-muted-foreground">
        Requester: {ticket.requester_name} ({ticket.requester_email})
      </div>
    </div>
  );
}