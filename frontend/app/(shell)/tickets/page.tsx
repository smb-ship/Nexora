"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { TicketTable } from "@/components/tickets/TicketTable";
import { TicketFilters } from "@/components/tickets/TicketFilters";
import { listTickets } from "@/lib/api/tickets";
import type { Ticket, TicketStatus, TicketPriority } from "@/types/ticket";

export default function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<TicketStatus | "all">("all");
  const [priority, setPriority] = useState<TicketPriority | "all">("all");

  useEffect(() => {
    setLoading(true);
    listTickets({
      status: status === "all" ? undefined : status,
      priority: priority === "all" ? undefined : priority,
    })
      .then(setTickets)
      .finally(() => setLoading(false));
  }, [status, priority]);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Tickets</h1>
        <Link href="/tickets/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Ticket
          </Button>
        </Link>
      </div>

      <TicketFilters
        status={status}
        priority={priority}
        onStatusChange={setStatus}
        onPriorityChange={setPriority}
      />

      {loading ? (
        <div className="text-muted-foreground">Loading tickets…</div>
      ) : (
        <TicketTable tickets={tickets} />
      )}
    </div>
  );
}