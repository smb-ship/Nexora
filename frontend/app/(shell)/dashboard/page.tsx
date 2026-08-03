"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Ticket, Inbox, CheckCircle2, MessageCircle, BookOpen, Workflow,
  Plus, Sparkles,
} from "lucide-react";
import { getDashboardSummary, type DashboardSummary } from "@/services/dashboard";
import { formatEventDescription } from "@/lib/format-event-description";

const STATUS_COLORS: Record<string, string> = {
  open: "#22c55e",
  pending: "#eab308",
  on_hold: "#f97316",
  resolved: "#3b82f6",
  closed: "#6b7280",
};

const PRIORITY_COLORS: Record<string, string> = {
  low: "#6b7280",
  medium: "#3b82f6",
  high: "#f97316",
  urgent: "#ef4444",
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardSummary()
      .then(setData)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load dashboard"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col gap-1">
      <div>
        <h1 className="text-xl font-semibold text-foreground tracking-tight">Dashboard</h1>
        <p className="text-sm text-foreground-muted">Mission control overview.</p>
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-500/30 bg-red-500/5 p-4 text-sm text-red-500">
          Failed to load dashboard: {error}
        </div>
      )}

      {loading && <KPIGridSkeleton />}

      {data && !loading && (
        <>
          <KPIGrid data={data} />
          <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
            <div className="lg:col-span-2 flex flex-col gap-4">
              <StatusChartCard charts={data.charts} />
              <RecentTicketsCard tickets={data.recent_tickets} />
            </div>
            <div className="flex flex-col gap-4">
              <PriorityDonutCard charts={data.charts} />
              <ActivityFeedCard events={data.recent_events} />
            </div>
          </div>
          <QuickActions />
        </>
      )}

      {!loading && !error && data && data.recent_tickets.length === 0 && (
        <p className="mt-6 text-sm text-foreground-muted">
          No tickets yet — once tickets start coming in, this dashboard will fill up with live data.
        </p>
      )}
    </div>
  );
}

// --- KPI Cards ---

function KPIGrid({ data }: { data: DashboardSummary }) {
  const cards = [
    { icon: Ticket, label: "Total Tickets", value: data.metrics.total_tickets, subtitle: `${data.metrics.tickets_today} today` },
    { icon: Inbox, label: "Open Tickets", value: data.metrics.open_tickets, subtitle: `${data.metrics.tickets_this_week} this week` },
    { icon: CheckCircle2, label: "Resolved Tickets", value: data.metrics.closed_tickets, subtitle: `${data.metrics.tickets_this_month} this month` },
    { icon: MessageCircle, label: "Live Chat", value: data.counts.live_chat_conversations, subtitle: "open conversations" },
    { icon: BookOpen, label: "Knowledge Articles", value: data.counts.knowledge_articles_published, subtitle: "published" },
    { icon: Workflow, label: "Automations", value: data.counts.automation_workflows_active, subtitle: `of ${data.counts.automation_workflows_total} total` },
  ];

  return (
    <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
      {cards.map((c) => (
        <div
          key={c.label}
          className="group rounded-lg border border-border p-4 transition-all hover:border-foreground/30 hover:shadow-lg hover:-translate-y-0.5"
        >
          <div className="flex items-center justify-between">
            <c.icon className="h-4 w-4 text-foreground-muted transition-colors group-hover:text-foreground" />
            {/* Trend indicator placeholder — no historical baseline exists
                yet to compute a real delta against, so this is an honest
                neutral placeholder rather than a fabricated number. */}
            <span className="text-[10px] text-foreground-subtle">—</span>
          </div>
          <p className="mt-2 text-2xl font-semibold text-foreground">{c.value}</p>
          <p className="text-xs text-foreground-muted">{c.label}</p>
          <p className="mt-0.5 text-[11px] text-foreground-subtle">{c.subtitle}</p>
        </div>
      ))}
    </div>
  );
}

function KPIGridSkeleton() {
  return (
    <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="rounded-lg border border-border p-4 animate-pulse">
          <div className="h-4 w-4 rounded bg-foreground/10" />
          <div className="mt-3 h-6 w-12 rounded bg-foreground/10" />
          <div className="mt-2 h-3 w-20 rounded bg-foreground/10" />
        </div>
      ))}
    </div>
  );
}

// --- Ticket Status Chart (simple horizontal bar breakdown, no new chart
// library dependency — Charts.tsx wasn't available to inspect this
// session, so this uses plain divs rather than guessing at its API) ---

function StatusChartCard({ charts }: { charts: DashboardSummary["charts"] }) {
  const total = charts.tickets_by_status.reduce((sum, s) => sum + s.count, 0);
  return (
    <div className="rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold text-foreground">Ticket Status</h2>
      <div className="mt-4 flex flex-col gap-3">
        {charts.tickets_by_status.length === 0 && (
          <p className="text-sm text-foreground-muted">No ticket data yet.</p>
        )}
        {charts.tickets_by_status.map((s) => {
          const pct = total > 0 ? Math.round((s.count / total) * 100) : 0;
          return (
            <div key={s.key}>
              <div className="flex items-center justify-between text-xs">
                <span className="capitalize text-foreground-muted">{s.key.replace("_", " ")}</span>
                <span className="text-foreground">{s.count}</span>
              </div>
              <div className="mt-1 h-2 w-full rounded-full bg-foreground/5">
                <div
                  className="h-2 rounded-full transition-all"
                  style={{ width: `${pct}%`, backgroundColor: STATUS_COLORS[s.key] || "#6b7280" }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// --- Priority Donut (CSS conic-gradient — no chart lib dependency) ---

function PriorityDonutCard({ charts }: { charts: DashboardSummary["charts"] }) {
  const total = charts.tickets_by_priority.reduce((sum, p) => sum + p.count, 0);
  let cumulative = 0;
  const segments = charts.tickets_by_priority.map((p) => {
    const start = total > 0 ? (cumulative / total) * 360 : 0;
    cumulative += p.count;
    const end = total > 0 ? (cumulative / total) * 360 : 0;
    return { ...p, start, end, color: PRIORITY_COLORS[p.key] || "#6b7280" };
  });

  const gradient = total > 0
    ? `conic-gradient(${segments.map((s) => `${s.color} ${s.start}deg ${s.end}deg`).join(", ")})`
    : "conic-gradient(#27272a 0deg 360deg)";

  return (
    <div className="rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold text-foreground">Priority Breakdown</h2>
      <div className="mt-4 flex items-center gap-4">
        <div
          className="h-24 w-24 shrink-0 rounded-full"
          style={{ background: gradient, mask: "radial-gradient(circle, transparent 55%, black 56%)", WebkitMask: "radial-gradient(circle, transparent 55%, black 56%)" }}
        />
        <div className="flex flex-col gap-1.5">
          {charts.tickets_by_priority.length === 0 && (
            <p className="text-xs text-foreground-muted">No data yet.</p>
          )}
          {segments.map((s) => (
            <div key={s.key} className="flex items-center gap-2 text-xs">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: s.color }} />
              <span className="capitalize text-foreground-muted">{s.key}</span>
              <span className="text-foreground">{s.count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// --- Recent Tickets Table ---

function RecentTicketsCard({ tickets }: { tickets: DashboardSummary["recent_tickets"] }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold text-foreground">Recent Tickets</h2>
      {tickets.length === 0 ? (
        <p className="mt-3 text-sm text-foreground-muted">No tickets yet.</p>
      ) : (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="text-foreground-subtle">
                <th className="pb-2 font-medium">Subject</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium">Priority</th>
                <th className="pb-2 font-medium">Requester</th>
                <th className="pb-2 font-medium">Agent</th>
                <th className="pb-2 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.id} className="border-t border-border">
                  <td colSpan={6} className="p-0">
                    <Link
                      href={`/tickets/${t.id}`}
                      className="flex items-center gap-0 py-2 hover:bg-foreground/5 [&>span]:px-1 [&>span]:py-2"
                    >
                      <span className="w-2/5 truncate text-foreground">{t.subject}</span>
                      <span className="w-1/6">
                        <span
                          className="rounded px-1.5 py-0.5 text-[10px] capitalize"
                          style={{
                            backgroundColor: `${STATUS_COLORS[t.status] || "#6b7280"}22`,
                            color: STATUS_COLORS[t.status] || "#6b7280",
                          }}
                        >
                          {t.status.replace("_", " ")}
                        </span>
                      </span>
                      <span className="w-1/6 capitalize text-foreground-muted">{t.priority}</span>
                      <span className="w-1/6 truncate text-foreground-muted">{t.requester_name}</span>
                      <span className="w-1/6 truncate text-foreground-muted">{t.assigned_to_name || "—"}</span>
                      <span className="w-1/6 whitespace-nowrap text-foreground-subtle">
                        {new Date(t.created_at).toLocaleDateString()}
                      </span>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// --- Activity Feed ---

function ActivityFeedCard({ events }: { events: DashboardSummary["recent_events"] }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold text-foreground">Recent Activity</h2>
      <div className="mt-3 flex flex-col gap-3">
        {events.length === 0 && <p className="text-sm text-foreground-muted">No recent activity.</p>}
        {events.map((e) => (
          <div key={e.event_id} className="flex items-start gap-2 text-xs">
            <Sparkles className="mt-0.5 h-3 w-3 shrink-0 text-foreground-subtle" />
            <div className="flex-1">
              <p className="text-foreground">{formatEventDescription(e)}</p>
              <p className="text-foreground-subtle">{new Date(e.created_at).toLocaleString()}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Quick Actions ---

function QuickActions() {
  const actions = [
    { label: "Create Ticket", href: "/tickets/new", icon: Plus },
    { label: "Open Live Chat", href: "/chat", icon: MessageCircle },
    { label: "Knowledge Hub", href: "/knowledge", icon: BookOpen },
    { label: "Automation", href: "/workflows", icon: Workflow },
    { label: "Integrations", href: "/automation", icon: Workflow },
  ];

  return (
    <div className="mt-6">
      <h2 className="text-sm font-semibold text-foreground">Quick Actions</h2>
      <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
        {actions.map((a) => (
          <Link
            key={a.label}
            href={a.href}
            className="flex flex-col items-center gap-2 rounded-lg border border-border p-4 text-center transition-all hover:border-foreground/30 hover:-translate-y-0.5 hover:shadow-lg"
          >
            <a.icon className="h-5 w-5 text-foreground-muted" />
            <span className="text-xs font-medium text-foreground">{a.label}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}