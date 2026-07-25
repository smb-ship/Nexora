"use client";

import { useEffect, useState, useCallback } from "react";
import { TicketTable } from "@/components/tickets/TicketTable";
import { InboxStateFilters } from "@/components/tickets/InboxStateFilters";
import { TicketSearchInput } from "@/components/tickets/TicketSearchInput";
import { Button } from "@/components/ui/button";
import { listTickets } from "@/lib/api/tickets";
import type { Ticket, InboxState, TicketListFilters } from "@/types/ticket";

const PAGE_SIZE = 25;

export default function InboxPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [state, setState] = useState<InboxState>("all");
  const [search, setSearch] = useState("");
  const [skip, setSkip] = useState(0);

  const fetchTickets = useCallback(() => {
    const filters: TicketListFilters = { skip, limit: PAGE_SIZE };
    if (search) filters.search = search;

    if (state === "unread") filters.unread = true;
    else if (state === "pending") filters.status = "pending";
    else if (state === "archived") filters.archived = true;
    // "replied" and "all" have no direct query param filter for
    // status/unread/archived — "replied" is filtered client-side below,
    // since it's a computed field not indexed for server-side filtering.
    // Flagged as technical debt: moves to a server-side filter once
    // Ticket gets a materialized last-reply-author column.

    setLoading(true);
    listTickets(filters)
      .then((result) => {
        setTickets(state === "replied" ? result.filter((t) => t.replied) : result);
      })
      .finally(() => setLoading(false));
  }, [state, search, skip]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  useEffect(() => {
    setSkip(0);
  }, [state, search]);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Inbox</h1>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <InboxStateFilters value={state} onChange={setState} />
        <div className="w-full sm:w-72">
          <TicketSearchInput onSearch={setSearch} />
        </div>
      </div>

      {loading ? (
        <div className="text-muted-foreground">Loading tickets…</div>
      ) : (
        <>
          <TicketTable tickets={tickets} />
          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              disabled={skip === 0}
              onClick={() => setSkip((s) => Math.max(0, s - PAGE_SIZE))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={tickets.length < PAGE_SIZE}
              onClick={() => setSkip((s) => s + PAGE_SIZE)}
            >
              Next
            </Button>
          </div>
        </>
      )}
    </div>
  );
}