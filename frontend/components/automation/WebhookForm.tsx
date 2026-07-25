"use client";

import { useState } from "react";
import type { OutgoingWebhook } from "@/services/automationDashboard";

export interface WebhookFormValues {
  name: string;
  target_url: string;
  event_types: string[];
  integration_type: string;
}

interface WebhookFormProps {
  initial?: OutgoingWebhook;
  submitting?: boolean;
  onSubmit: (values: WebhookFormValues) => void;
  onCancel: () => void;
}

const INTEGRATION_TYPES = ["generic", "discord", "slack", "n8n"];

// Mirrors app.core.events.EventType. Ticket-shaped members mirror
// WorkflowTriggerType 1:1; the rest are webhook/n8n-only.
const TICKET_EVENT_TYPES = [
  "ticket_created",
  "ticket_status_changed",
  "ticket_priority_changed",
  "ticket_assigned",
  "ticket_unassigned",
  "ticket_comment_added",
  "ticket_sentiment_changed",
  "ticket_idle",
];

const OTHER_EVENT_TYPES = [
  "email_received",
  "email_sent",
  "ai_completed",
  "customer_created",
  "workflow_executed",
];

export function WebhookForm({ initial, submitting, onSubmit, onCancel }: WebhookFormProps) {
  const [name, setName] = useState(initial?.name ?? "");
  const [targetUrl, setTargetUrl] = useState(initial?.target_url ?? "");
  const [integrationType, setIntegrationType] = useState(initial?.integration_type ?? "generic");
  const [eventTypes, setEventTypes] = useState<string[]>(initial?.event_types ?? []);

  function toggleEventType(type: string) {
    setEventTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit({ name, target_url: targetUrl, event_types: eventTypes, integration_type: integrationType });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mt-4 flex flex-col gap-4 rounded-lg border border-border p-4"
    >
      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-foreground-muted">Name</label>
        <input
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="rounded-md border border-border bg-transparent px-3 py-1.5 text-sm text-foreground"
          placeholder="e.g. Slack alerts"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-foreground-muted">Target URL</label>
        <input
          required
          type="url"
          value={targetUrl}
          onChange={(e) => setTargetUrl(e.target.value)}
          className="rounded-md border border-border bg-transparent px-3 py-1.5 text-sm text-foreground"
          placeholder="https://..."
        />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-foreground-muted">Integration Type</label>
        <select
          value={integrationType}
          onChange={(e) => setIntegrationType(e.target.value)}
          className="rounded-md border border-border bg-transparent px-3 py-1.5 text-sm text-foreground"
        >
          {INTEGRATION_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-2">
        <label className="text-xs font-medium text-foreground-muted">Event Types</label>

        <p className="text-xs text-foreground-subtle">Ticket events</p>
        <div className="flex flex-wrap gap-2">
          {TICKET_EVENT_TYPES.map((type) => (
            <EventTypeChip
              key={type}
              type={type}
              checked={eventTypes.includes(type)}
              onToggle={toggleEventType}
            />
          ))}
        </div>

        <p className="mt-1 text-xs text-foreground-subtle">Other events</p>
        <div className="flex flex-wrap gap-2">
          {OTHER_EVENT_TYPES.map((type) => (
            <EventTypeChip
              key={type}
              type={type}
              checked={eventTypes.includes(type)}
              onToggle={toggleEventType}
            />
          ))}
        </div>

        {eventTypes.length === 0 && (
          <p className="text-xs text-red-500">At least one event type is required.</p>
        )}
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting || eventTypes.length === 0}
          className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background disabled:opacity-50"
        >
          {submitting ? "Saving..." : initial ? "Save Changes" : "Create Webhook"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-foreground/5"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

function EventTypeChip({
  type,
  checked,
  onToggle,
}: {
  type: string;
  checked: boolean;
  onToggle: (type: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onToggle(type)}
      className={`rounded-md border px-2 py-1 text-xs font-medium ${
        checked
          ? "border-foreground bg-foreground text-background"
          : "border-border text-foreground-muted hover:bg-foreground/5"
      }`}
    >
      {type}
    </button>
  );
}