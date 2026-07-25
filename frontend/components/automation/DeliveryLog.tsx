"use client";

import { useEffect, useState } from "react";
import { getDeliveries, type WebhookDeliveryLog } from "@/services/automationDashboard";

const STATUS_STYLES: Record<WebhookDeliveryLog["status"], string> = {
  success: "bg-green-500/10 text-green-500",
  failed: "bg-red-500/10 text-red-500",
  retrying: "bg-yellow-500/10 text-yellow-500",
  pending: "bg-foreground/10 text-foreground-muted",
};

export function DeliveryLog({ webhookId }: { webhookId: string }) {
  const [deliveries, setDeliveries] = useState<WebhookDeliveryLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getDeliveries(webhookId)
      .then(setDeliveries)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load deliveries"))
      .finally(() => setLoading(false));
  }, [webhookId]);

  if (loading) return <p className="mt-2 text-xs text-foreground-muted">Loading deliveries...</p>;
  if (error) return <p className="mt-2 text-xs text-red-500">{error}</p>;
  if (deliveries.length === 0)
    return <p className="mt-2 text-xs text-foreground-muted">No deliveries yet.</p>;

  return (
    <div className="mt-2 flex flex-col gap-1.5 rounded-lg border border-border p-3">
      {deliveries.map((d) => (
        <div
          key={d.id}
          className="flex items-center justify-between gap-2 border-b border-border/50 pb-1.5 text-xs last:border-0 last:pb-0"
        >
          <span className="w-32 truncate text-foreground-muted">{d.event_type}</span>
          <span className={`rounded px-1.5 py-0.5 font-medium ${STATUS_STYLES[d.status]}`}>
            {d.status}
          </span>
          <span className="text-foreground-muted">attempts: {d.attempt_count}</span>
          <span className="text-foreground-muted">
            {d.response_status_code ?? "—"}
          </span>
          <span className="text-foreground-subtle">
            {new Date(d.created_at).toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  );
}