"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listCustomers, type CustomerListItem } from "@/services/customers";

const PAGE_SIZE = 20;

export default function CustomersPage() {
  const [data, setData] = useState<{ items: CustomerListItem[]; total: number } | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"" | "active" | "inactive">("");
  const [hasOpenFilter, setHasOpenFilter] = useState<"" | "true" | "false">("");
  const [sort, setSort] = useState("created_at");
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    listCustomers({
      q: search || undefined,
      status: statusFilter || undefined,
      has_open_tickets: hasOpenFilter === "" ? undefined : hasOpenFilter === "true",
      sort, order,
      skip: page * PAGE_SIZE, limit: PAGE_SIZE,
    })
      .then(setData)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load customers"))
      .finally(() => setLoading(false));
  }

  useEffect(load, [search, statusFilter, hasOpenFilter, sort, order, page]);

  function toggleSort(field: string) {
    if (sort === field) {
      setOrder(order === "asc" ? "desc" : "asc");
    } else {
      setSort(field);
      setOrder("desc");
    }
    setPage(0);
  }

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  return (
    <div className="flex flex-col gap-1">
      <div>
        <h1 className="text-xl font-semibold text-foreground tracking-tight">Customers</h1>
        <p className="text-sm text-foreground-muted">Customer relationship records.</p>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <input
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(0); }}
          placeholder="Search name or email..."
          className="flex-1 min-w-[200px] rounded-md border border-border bg-transparent px-3 py-1.5 text-sm text-foreground"
        />
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value as typeof statusFilter); setPage(0); }}
          className="rounded-md border border-border bg-transparent px-2 py-1.5 text-sm text-foreground"
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
        <select
          value={hasOpenFilter}
          onChange={(e) => { setHasOpenFilter(e.target.value as typeof hasOpenFilter); setPage(0); }}
          className="rounded-md border border-border bg-transparent px-2 py-1.5 text-sm text-foreground"
        >
          <option value="">Any ticket status</option>
          <option value="true">Has open tickets</option>
          <option value="false">No open tickets</option>
        </select>
      </div>

      {error && <p className="mt-4 text-sm text-red-500">{error}</p>}

      <div className="mt-4 overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs text-foreground-subtle">
              <th className="p-3 font-medium">Name</th>
              <SortableHeader label="Email" field="email" sort={sort} order={order} onClick={toggleSort} />
              <th className="p-3 font-medium">Status</th>
              <SortableHeader label="Open" field="open_tickets" sort={sort} order={order} onClick={toggleSort} />
              <SortableHeader label="Total" field="total_tickets" sort={sort} order={order} onClick={toggleSort} />
              <SortableHeader label="Last Seen" field="last_seen" sort={sort} order={order} onClick={toggleSort} />
              <SortableHeader label="Created" field="created_at" sort={sort} order={order} onClick={toggleSort} />
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={7} className="p-6 text-center text-sm text-foreground-muted">Loading...</td></tr>
            )}
            {!loading && data?.items.length === 0 && (
              <tr><td colSpan={7} className="p-6 text-center text-sm text-foreground-muted">No customers found.</td></tr>
            )}
            {!loading && data?.items.map((c) => (
              <tr key={c.id} className="border-b border-border last:border-0 hover:bg-foreground/5">
                <td className="p-0">
                  <Link href={`/customers/${c.id}`} className="flex items-center gap-3 p-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-foreground/10 text-xs font-medium text-foreground">
                      {(c.full_name || c.email).slice(0, 2).toUpperCase()}
                    </div>
                    <span className="font-medium text-foreground">{c.full_name || "—"}</span>
                  </Link>
                </td>
                <td className="p-3 text-foreground-muted">
                  <Link href={`/customers/${c.id}`}>{c.email}</Link>
                </td>
                <td className="p-3">
                  <span className={`rounded px-1.5 py-0.5 text-xs ${c.is_active ? "bg-green-500/10 text-green-500" : "bg-foreground/10 text-foreground-muted"}`}>
                    {c.is_active ? "active" : "inactive"}
                  </span>
                </td>
                <td className="p-3 text-foreground-muted">{c.open_tickets}</td>
                <td className="p-3 text-foreground-muted">{c.total_tickets}</td>
                <td className="p-3 text-foreground-subtle">{c.last_seen ? new Date(c.last_seen).toLocaleDateString() : "—"}</td>
                <td className="p-3 text-foreground-subtle">{new Date(c.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data && totalPages > 1 && (
        <div className="mt-3 flex items-center justify-between text-xs text-foreground-muted">
          <span>Page {page + 1} of {totalPages} ({data.total} total)</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="rounded-md border border-border px-2 py-1 disabled:opacity-40"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="rounded-md border border-border px-2 py-1 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function SortableHeader({
  label, field, sort, order, onClick,
}: { label: string; field: string; sort: string; order: string; onClick: (f: string) => void }) {
  const active = sort === field;
  return (
    <th
      onClick={() => onClick(field)}
      className={`p-3 cursor-pointer select-none font-medium hover:text-foreground ${active ? "text-foreground" : ""}`}
    >
      {label} {active && (order === "asc" ? "↑" : "↓")}
    </th>
  );
}