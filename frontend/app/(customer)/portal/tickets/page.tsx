"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import { customerPortalService } from "@/services/customerPortal";
import type { CustomerTicketListItem, CustomerTicketStatus } from "@/types/customerPortal";
import { StatusBadge, PriorityBadge } from "@/components/customer-portal/Badges";

const STATUS_OPTIONS: { value: CustomerTicketStatus | ""; label: string }[] = [
  { value: "", label: "All statuses" },
  { value: "open", label: "Open" },
  { value: "pending", label: "Pending" },
  { value: "on_hold", label: "On Hold" },
  { value: "resolved", label: "Resolved" },
  { value: "closed", label: "Closed" },
];

const LIMIT = 20;

export default function MyTicketsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [items, setItems] = useState<CustomerTicketListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState(searchParams.get("q") ?? "");
  const [status, setStatus] = useState<CustomerTicketStatus | "">(
    (searchParams.get("status") as CustomerTicketStatus) ?? ""
  );
  const [skip, setSkip] = useState(0);

  const load = useCallback(() => {
    setLoading(true);
    customerPortalService
      .listTickets({ q: q || undefined, status: status || undefined, skip, limit: LIMIT })
      .then((res) => {
        setItems(res.items);
        setTotal(res.total);
      })
      .finally(() => setLoading(false));
  }, [q, status, skip]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSkip(0);
    load();
  };

  const page = Math.floor(skip / LIMIT) + 1;
  const totalPages = Math.max(1, Math.ceil(total / LIMIT));

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-foreground">My Tickets</h1>
        <p className="text-sm text-foreground-muted">{total} ticket{total !== 1 ? "s" : ""} total</p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-muted" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search tickets..."
            className="w-full rounded-md border border-border bg-surface py-2 pl-10 pr-4 text-sm text-foreground placeholder:text-foreground-muted"
          />
        </form>
        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value as CustomerTicketStatus | "");
            setSkip(0);
          }}
          className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <p className="text-sm text-foreground-muted">Loading...</p>
      ) : items.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border py-12 text-center text-sm text-foreground-muted">
          No tickets match your filters.
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-surface-elevated text-left text-xs text-foreground-muted">
              <tr>
                <th className="px-4 py-2.5 font-medium">Subject</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
                <th className="px-4 py-2.5 font-medium">Priority</th>
                <th className="px-4 py-2.5 font-medium">Assigned Agent</th>
                <th className="px-4 py-2.5 font-medium">Created</th>
                <th className="px-4 py-2.5 font-medium">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {items.map((t) => (
                <tr
                  key={t.id}
                  onClick={() => router.push(`/portal/tickets/${t.id}`)}
                  className="cursor-pointer bg-surface hover:bg-surface-elevated"
                >
                  <td className="px-4 py-3 font-medium text-foreground">{t.subject}</td>
                  <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                  <td className="px-4 py-3"><PriorityBadge priority={t.priority} /></td>
                  <td className="px-4 py-3 text-foreground-muted">{t.assignee?.full_name ?? "Unassigned"}</td>
                  <td className="px-4 py-3 text-foreground-muted">{new Date(t.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3 text-foreground-muted">{new Date(t.updated_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-foreground-muted">
          <span>Page {page} of {totalPages}</span>
          <div className="flex gap-2">
            <button
              onClick={() => setSkip(Math.max(0, skip - LIMIT))}
              disabled={skip === 0}
              className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 disabled:opacity-40"
            >
              <ChevronLeft className="h-4 w-4" /> Prev
            </button>
            <button
              onClick={() => setSkip(skip + LIMIT)}
              disabled={page >= totalPages}
              className="flex items-center gap-1 rounded-md border border-border px-3 py-1.5 disabled:opacity-40"
            >
              Next <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}