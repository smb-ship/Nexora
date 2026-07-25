"use client";

import { useEffect, useState } from "react";
import { analyticsApi, DashboardMetrics, ChartsBundle } from "@/services/analytics";
import {
  GroupBarChart, DailyTrendChart, SentimentPieChart, TopAgentsChart,
} from "@/components/analytics/Charts";

export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [charts, setCharts] = useState<ChartsBundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([analyticsApi.dashboard(), analyticsApi.charts()])
      .then(([m, c]) => {
        setMetrics(m);
        setCharts(c);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load analytics"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground tracking-tight">Analytics</h1>
          <p className="text-sm text-foreground-muted">
            Performance overview across tickets, AI, and workflows.
          </p>
        </div>
        <div className="flex gap-2">
          <a href={analyticsApi.exportUrl("csv")} className="rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-foreground/5">
            Export CSV
          </a>
          <a href={analyticsApi.exportUrl("json")} className="rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-foreground/5">
            Export JSON
          </a>
        </div>
      </div>

      {error && <p className="mt-4 text-sm text-red-500">{error}</p>}
      {loading && <p className="mt-4 text-sm text-foreground-muted">Loading analytics...</p>}

      {metrics && (
        <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
          <MetricCard label="Total Tickets" value={metrics.total_tickets} />
          <MetricCard label="Open" value={metrics.open_tickets} />
          <MetricCard label="Closed" value={metrics.closed_tickets} />
          <MetricCard label="Today" value={metrics.tickets_today} />
          <MetricCard label="This Week" value={metrics.tickets_this_week} />
          <MetricCard label="This Month" value={metrics.tickets_this_month} />
          <MetricCard label="Avg Resolution" value={formatDuration(metrics.avg_resolution_seconds)} />
          <MetricCard label="Avg First Response" value={formatDuration(metrics.avg_first_response_seconds)} />
          <MetricCard label="Avg Reply Time" value={formatDuration(metrics.avg_reply_seconds)} />
          <MetricCard label="AI Analyses" value={metrics.ai_analyses_performed} />
          <MetricCard label="Workflow Runs" value={metrics.workflow_stats.total_executions} />
          <MetricCard label="Workflow Success" value={`${metrics.workflow_stats.success_rate}%`} />
        </div>
      )}

      {charts && (
        <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
          <DailyTrendChart data={charts.daily_tickets} />
          <SentimentPieChart data={charts.sentiment_distribution} />
          <GroupBarChart title="Tickets by Status" data={charts.tickets_by_status} />
          <GroupBarChart title="Tickets by Priority" data={charts.tickets_by_priority} />
          <GroupBarChart title="Tickets by Source" data={charts.tickets_by_source} />
          <GroupBarChart title="Tickets by Team" data={charts.tickets_by_team} />
          <TopAgentsChart data={charts.tickets_by_agent} />
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <p className="text-xs text-foreground-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-foreground">{value}</p>
    </div>
  );
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "—";
  const hours = seconds / 3600;
  if (hours < 1) return `${Math.round(seconds / 60)}m`;
  if (hours < 24) return `${hours.toFixed(1)}h`;
  return `${(hours / 24).toFixed(1)}d`;
}