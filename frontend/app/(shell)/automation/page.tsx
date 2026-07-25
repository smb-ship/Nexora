"use client";

import { useEffect, useState } from "react";
import {
  getAutomationDashboard,
  listWebhooks,
  createWebhook,
  updateWebhook,
  deleteWebhook,
  type AutomationDashboard,
  type OutgoingWebhook,
} from "@/services/automationDashboard";
import {
  listWebhookKeys,
  createWebhookKey,
  revokeWebhookKey,
  type IncomingWebhookKey,
} from "@/services/integrations";
import { WebhookForm, type WebhookFormValues } from "@/components/automation/WebhookForm";
import { DeliveryLog } from "@/components/automation/DeliveryLog";

export default function AutomationPage() {
  const [dashboard, setDashboard] = useState<AutomationDashboard | null>(null);
  const [webhooks, setWebhooks] = useState<OutgoingWebhook[]>([]);
  const [keys, setKeys] = useState<IncomingWebhookKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [formMode, setFormMode] = useState<"none" | "create" | string>("none");
  const [submitting, setSubmitting] = useState(false);
  const [justCreatedSecret, setJustCreatedSecret] = useState<{ id: string; secret: string } | null>(
    null
  );
  const [expandedDeliveries, setExpandedDeliveries] = useState<string | null>(null);

  const [newKeyName, setNewKeyName] = useState("");
  const [keySubmitting, setKeySubmitting] = useState(false);
  const [justCreatedKey, setJustCreatedKey] = useState<{ id: string; plaintext: string } | null>(null);

  function loadAll() {
    setLoading(true);
    Promise.all([getAutomationDashboard(), listWebhooks(), listWebhookKeys()])
      .then(([d, w, k]) => {
        setDashboard(d);
        setWebhooks(w);
        setKeys(k);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load automation data"))
      .finally(() => setLoading(false));
  }

  useEffect(loadAll, []);

  async function handleCreate(values: WebhookFormValues) {
    setSubmitting(true);
    try {
      const created = await createWebhook(values);
      setJustCreatedSecret({ id: created.id, secret: created.signing_secret });
      setFormMode("none");
      loadAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create webhook");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleUpdate(id: string, values: WebhookFormValues) {
    setSubmitting(true);
    try {
      await updateWebhook(id, values);
      setFormMode("none");
      loadAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update webhook");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this webhook? This cannot be undone.")) return;
    try {
      await deleteWebhook(id);
      loadAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete webhook");
    }
  }

  async function handleCreateKey(e: React.FormEvent) {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    setKeySubmitting(true);
    try {
      const created = await createWebhookKey(newKeyName.trim());
      setJustCreatedKey({ id: created.id, plaintext: created.plaintext_key });
      setNewKeyName("");
      loadAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create key");
    } finally {
      setKeySubmitting(false);
    }
  }

  async function handleRevokeKey(id: string) {
    if (!confirm("Revoke this key? Any integration using it will stop working immediately.")) return;
    try {
      await revokeWebhookKey(id);
      loadAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to revoke key");
    }
  }

  const editingWebhook =
    formMode !== "none" && formMode !== "create" ? webhooks.find((w) => w.id === formMode) : undefined;

  return (
    <div className="flex flex-col gap-1">
      <div>
        <h1 className="text-xl font-semibold text-foreground tracking-tight">Integrations</h1>
        <p className="text-sm text-foreground-muted">
          Outgoing webhooks, event bus activity, and connected services.
        </p>
      </div>

      {error && <p className="mt-4 text-sm text-red-500">{error}</p>}
      {loading && <p className="mt-4 text-sm text-foreground-muted">Loading...</p>}

      {dashboard && (
        <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
          <MetricCard label="Connected Services" value={dashboard.connected_services.length} />
          <MetricCard label="Pending Retries" value={dashboard.pending_retries} />
          <MetricCard label="Deliveries (24h)" value={dashboard.deliveries_last_24h} />
          <MetricCard label="Failures (24h)" value={dashboard.failures_last_24h} />
        </div>
      )}

      {/* Webhooks management */}
      <div className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-foreground">Webhooks</h2>
          {formMode === "none" && (
            <button
              onClick={() => setFormMode("create")}
              className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background"
            >
              New Webhook
            </button>
          )}
        </div>

        {justCreatedSecret && (
          <div className="mt-4 rounded-lg border border-border bg-foreground/5 p-4">
            <p className="text-xs font-medium text-foreground-muted">
              Signing secret — shown once, copy it now:
            </p>
            <div className="mt-1 flex items-center gap-2">
              <code className="flex-1 truncate rounded bg-background px-2 py-1 text-xs">
                {justCreatedSecret.secret}
              </code>
              <button
                onClick={() => navigator.clipboard.writeText(justCreatedSecret.secret)}
                className="rounded-md border border-border px-2 py-1 text-xs hover:bg-foreground/5"
              >
                Copy
              </button>
              <button
                onClick={() => setJustCreatedSecret(null)}
                className="rounded-md border border-border px-2 py-1 text-xs hover:bg-foreground/5"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {formMode === "create" && (
          <WebhookForm
            submitting={submitting}
            onSubmit={handleCreate}
            onCancel={() => setFormMode("none")}
          />
        )}
        {editingWebhook && (
          <WebhookForm
            initial={editingWebhook}
            submitting={submitting}
            onSubmit={(values) => handleUpdate(editingWebhook.id, values)}
            onCancel={() => setFormMode("none")}
          />
        )}

        <div className="mt-4 flex flex-col gap-2">
          {webhooks.map((w) => (
            <div key={w.id} className="rounded-lg border border-border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {w.name}{" "}
                    <span className="ml-2 rounded bg-foreground/10 px-1.5 py-0.5 text-xs text-foreground-muted">
                      {w.integration_type}
                    </span>
                    {!w.is_active && (
                      <span className="ml-2 rounded bg-red-500/10 px-1.5 py-0.5 text-xs text-red-500">
                        inactive
                      </span>
                    )}
                  </p>
                  <p className="mt-0.5 text-xs text-foreground-muted">{w.target_url}</p>
                  <p className="mt-0.5 text-xs text-foreground-subtle">
                    {w.event_types.join(", ") || "no event types configured"}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setExpandedDeliveries(expandedDeliveries === w.id ? null : w.id)}
                    className="rounded-md border border-border px-2 py-1 text-xs hover:bg-foreground/5"
                  >
                    {expandedDeliveries === w.id ? "Hide Deliveries" : "View Deliveries"}
                  </button>
                  <button
                    onClick={() => setFormMode(w.id)}
                    className="rounded-md border border-border px-2 py-1 text-xs hover:bg-foreground/5"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(w.id)}
                    className="rounded-md border border-border px-2 py-1 text-xs text-red-500 hover:bg-red-500/5"
                  >
                    Delete
                  </button>
                </div>
              </div>
              {expandedDeliveries === w.id && <DeliveryLog webhookId={w.id} />}
            </div>
          ))}
          {webhooks.length === 0 && !loading && (
            <p className="text-sm text-foreground-muted">No webhooks configured yet.</p>
          )}
        </div>
      </div>

      {/* n8n / incoming integration keys */}
      <div className="mt-8">
        <h2 className="text-sm font-semibold text-foreground">n8n Integration Keys</h2>
        <p className="mt-1 text-xs text-foreground-muted">
          Keys presented via the X-Nexora-Webhook-Key header by external callers (e.g. n8n)
          to create tickets or add comments.
        </p>

        {justCreatedKey && (
          <div className="mt-4 rounded-lg border border-border bg-foreground/5 p-4">
            <p className="text-xs font-medium text-foreground-muted">
              Key — shown once, copy it now:
            </p>
            <div className="mt-1 flex items-center gap-2">
              <code className="flex-1 truncate rounded bg-background px-2 py-1 text-xs">
                {justCreatedKey.plaintext}
              </code>
              <button
                onClick={() => navigator.clipboard.writeText(justCreatedKey.plaintext)}
                className="rounded-md border border-border px-2 py-1 text-xs hover:bg-foreground/5"
              >
                Copy
              </button>
              <button
                onClick={() => setJustCreatedKey(null)}
                className="rounded-md border border-border px-2 py-1 text-xs hover:bg-foreground/5"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        <form onSubmit={handleCreateKey} className="mt-4 flex gap-2">
          <input
            required
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
            placeholder="Key name (e.g. n8n production)"
            className="flex-1 rounded-md border border-border bg-transparent px-3 py-1.5 text-sm text-foreground"
          />
          <button
            type="submit"
            disabled={keySubmitting}
            className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background disabled:opacity-50"
          >
            {keySubmitting ? "Creating..." : "Create Key"}
          </button>
        </form>

        <div className="mt-4 flex flex-col gap-2">
          {keys.map((k) => (
            <div
              key={k.id}
              className="flex items-center justify-between rounded-lg border border-border p-4"
            >
              <div>
                <p className="text-sm font-medium text-foreground">
                  {k.name}
                  {!k.is_active && (
                    <span className="ml-2 rounded bg-red-500/10 px-1.5 py-0.5 text-xs text-red-500">
                      revoked
                    </span>
                  )}
                </p>
                <p className="mt-0.5 text-xs text-foreground-muted">
                  Created {new Date(k.created_at).toLocaleDateString()}
                  {" · "}
                  Last used{" "}
                  {k.last_used_at ? new Date(k.last_used_at).toLocaleString() : "never"}
                </p>
              </div>
              {k.is_active && (
                <button
                  onClick={() => handleRevokeKey(k.id)}
                  className="rounded-md border border-border px-2 py-1 text-xs text-red-500 hover:bg-red-500/5"
                >
                  Revoke
                </button>
              )}
            </div>
          ))}
          {keys.length === 0 && !loading && (
            <p className="text-sm text-foreground-muted">No integration keys yet.</p>
          )}
        </div>
      </div>

      {/* Recent event feed */}
      {dashboard && (
        <div className="mt-8">
          <h2 className="text-sm font-semibold text-foreground">Recent Events</h2>
          <div className="mt-4 flex flex-col gap-2">
            {dashboard.recent_events.map((ev) => (
              <div
                key={ev.event_id}
                className="flex items-center justify-between rounded-lg border border-border p-3 text-sm"
              >
                <span className="font-medium text-foreground">{ev.event_type}</span>
                <span className="text-xs text-foreground-muted">
                  {new Date(ev.created_at).toLocaleString()}
                </span>
              </div>
            ))}
            {dashboard.recent_events.length === 0 && (
              <p className="text-sm text-foreground-muted">No recent events.</p>
            )}
          </div>
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