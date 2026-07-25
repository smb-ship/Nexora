"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, Inbox, CheckCircle2, Archive, TicketIcon } from "lucide-react";
import { customerPortalService } from "@/services/customerPortal";
import type { CustomerDashboardStats } from "@/types/customerPortal";
import { StatusBadge, PriorityBadge } from "@/components/customer-portal/Badges";

function StatCard({ label, value, icon: Icon }: { label: string; value: number; icon: React.ElementType }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-foreground-muted">{label}</span>
        <Icon className="h-4 w-4 text-foreground-muted" />
      </div>
      <p className="mt-2 text-2xl font-semibold text-foreground">{value}</p>
    </div>
  );
}

export default function CustomerDashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<CustomerDashboardStats | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    customerPortalService
      .dashboard()
      .then(setStats)
      .finally(() => setLoading(false));
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    router.push(`/portal/tickets?q=${encodeURIComponent(search)}`);
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-foreground">Welcome back</h1>
        <p className="text-sm text-foreground-muted">Here's an overview of your support activity.</p>
      </div>

      <form onSubmit={handleSearch} className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-muted" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search your tickets..."
          className="w-full rounded-md border border-border bg-surface py-2.5 pl-10 pr-4 text-sm text-foreground placeholder:text-foreground-muted"
        />
      </form>

      {loading ? (
        <p className="text-sm text-foreground-muted">Loading...</p>
      ) : stats ? (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label="Total Tickets" value={stats.total_tickets} icon={TicketIcon} />
            <StatCard label="Open" value={stats.open_tickets} icon={Inbox} />
            <StatCard label="Resolved" value={stats.resolved_tickets} icon={CheckCircle2} />
            <StatCard label="Closed" value={stats.closed_tickets} icon={Archive} />
          </div>

          <div>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-medium text-foreground">Recent Tickets</h2>
              <Link href="/portal/tickets" className="text-sm text-primary hover:underline">
                View all
              </Link>
            </div>

            {stats.recent_tickets.length === 0 ? (
              <div className="rounded-lg border border-dashed border-border py-12 text-center text-sm text-foreground-muted">
                No tickets yet.{" "}
                <Link href="/portal/tickets/new" className="text-primary hover:underline">
                  Create your first ticket
                </Link>
              </div>
            ) : (
              <div className="space-y-2">
                {stats.recent_tickets.map((t) => (
                  <Link
                    key={t.id}
                    href={`/portal/tickets/${t.id}`}
                    className="flex items-center justify-between rounded-lg border border-border bg-surface px-4 py-3 hover:bg-surface-elevated"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-foreground">{t.subject}</p>
                      <p className="text-xs text-foreground-muted">
                        Updated {new Date(t.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <PriorityBadge priority={t.priority} />
                      <StatusBadge status={t.status} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </>
      ) : null}
    </div>
  );
}