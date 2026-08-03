"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getCustomer, getCustomerTickets, getCustomerChats, getCustomerTimeline,
  listCustomerNotes, createCustomerNote, updateCustomerNote, deleteCustomerNote,
  type CustomerDetail, type CustomerTicket, type CustomerChatSummary,
  type TimelineItem, type CustomerNote,
} from "@/services/customers";
import { getConversation, type ChatConversationDetail } from "@/services/chat";

const STATUS_COLORS: Record<string, string> = {
  open: "#22c55e", pending: "#eab308", on_hold: "#f97316", resolved: "#3b82f6", closed: "#6b7280",
};
const PRIORITY_COLORS: Record<string, string> = {
  low: "#6b7280", medium: "#3b82f6", high: "#f97316", urgent: "#ef4444",
};

function formatSeconds(s: number | null): string {
  if (s === null) return "—";
  if (s < 60) return `${Math.round(s)}s`;
  if (s < 3600) return `${Math.round(s / 60)}m`;
  return `${(s / 3600).toFixed(1)}h`;
}

export default function CustomerDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [customer, setCustomer] = useState<CustomerDetail | null>(null);
  const [tickets, setTickets] = useState<CustomerTicket[]>([]);
  const [chats, setChats] = useState<CustomerChatSummary[]>([]);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [notes, setNotes] = useState<CustomerNote[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getCustomer(id), getCustomerTickets(id), getCustomerChats(id),
      getCustomerTimeline(id), listCustomerNotes(id),
    ])
      .then(([c, t, ch, tl, n]) => {
        setCustomer(c); setTickets(t); setChats(ch); setTimeline(tl); setNotes(n);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load customer"))
      .finally(() => setLoading(false));
  }, [id]);

  function reloadNotes() {
    listCustomerNotes(id).then(setNotes).catch(() => {});
  }

  if (loading) return <CustomerDetailSkeleton />;

  if (error || !customer) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border py-16 text-center">
        <p className="text-sm text-foreground-muted">{error || "Customer not found."}</p>
        <Link href="/crm" className="text-sm text-foreground hover:underline">
          ← Back to Customers
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <Link href="/crm" className="text-xs text-foreground-muted hover:underline">
        ← Back to Customers
      </Link>
      <CustomerHeader customer={customer} />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 flex flex-col gap-4">
          <TicketsSection tickets={tickets} />
          <ChatHistorySection chats={chats} />
        </div>
        <div className="flex flex-col gap-4">
          <TimelineSection items={timeline} />
          <NotesSection customerId={id} notes={notes} onChange={reloadNotes} />
        </div>
      </div>
    </div>
  );
}

function CustomerDetailSkeleton() {
  return (
    <div className="flex animate-pulse flex-col gap-6">
      <div className="h-3 w-28 rounded bg-foreground/10" />
      <div className="rounded-lg border border-border p-5">
        <div className="flex items-start gap-4">
          <div className="h-14 w-14 shrink-0 rounded-full bg-foreground/10" />
          <div className="flex-1">
            <div className="h-5 w-40 rounded bg-foreground/10" />
            <div className="mt-2 h-4 w-56 rounded bg-foreground/10" />
          </div>
        </div>
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-16 rounded-lg border border-border" />
          ))}
        </div>
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="h-48 rounded-lg border border-border lg:col-span-2" />
        <div className="h-48 rounded-lg border border-border" />
      </div>
    </div>
  );
}

function CustomerHeader({ customer }: { customer: CustomerDetail }) {
  return (
    <div className="rounded-lg border border-border p-5">
      <div className="flex items-start gap-4">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-foreground/10 text-lg font-medium text-foreground">
          {(customer.full_name || customer.email).slice(0, 2).toUpperCase()}
        </div>
        <div className="flex-1">
          <h1 className="text-lg font-semibold text-foreground">{customer.full_name || "Unnamed Customer"}</h1>
          <p className="text-sm text-foreground-muted">{customer.email}</p>
          <p className="mt-1 text-xs text-foreground-subtle">
            Customer since {new Date(customer.created_at).toLocaleDateString()}
          </p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Lifetime Tickets" value={customer.stats.lifetime_tickets} />
        <StatCard label="Open Issues" value={customer.stats.open_issues} />
        <StatCard
          label="Resolution Rate"
          value={customer.stats.resolution_rate !== null ? `${Math.round(customer.stats.resolution_rate * 100)}%` : "—"}
        />
        <StatCard label="Avg Response" value={formatSeconds(customer.stats.avg_response_seconds)} />
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-border p-3 transition-colors hover:border-foreground/30">
      <p className="text-lg font-semibold text-foreground">{value}</p>
      <p className="text-xs text-foreground-muted">{label}</p>
    </div>
  );
}

function TicketsSection({ tickets }: { tickets: CustomerTicket[] }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold text-foreground">Tickets</h2>
      {tickets.length === 0 ? (
        <p className="mt-2 text-sm text-foreground-muted">No tickets yet.</p>
      ) : (
        <div className="mt-3 flex flex-col gap-2">
          {tickets.map((t) => (
            <Link
              key={t.id}
              href={`/tickets/${t.id}`}
              className="flex items-center justify-between rounded-md border border-border p-3 transition-colors hover:bg-foreground/5"
            >
              <span className="truncate text-sm text-foreground">{t.subject}</span>
              <div className="flex shrink-0 gap-2">
                <span
                  className="rounded px-1.5 py-0.5 text-[10px] capitalize"
                  style={{ backgroundColor: `${PRIORITY_COLORS[t.priority] || "#6b7280"}22`, color: PRIORITY_COLORS[t.priority] || "#6b7280" }}
                >
                  {t.priority}
                </span>
                <span
                  className="rounded px-1.5 py-0.5 text-[10px] capitalize"
                  style={{ backgroundColor: `${STATUS_COLORS[t.status] || "#6b7280"}22`, color: STATUS_COLORS[t.status] || "#6b7280" }}
                >
                  {t.status.replace("_", " ")}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function ChatHistorySection({ chats }: { chats: CustomerChatSummary[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [detail, setDetail] = useState<ChatConversationDetail | null>(null);

  async function toggle(id: string) {
    if (expanded === id) {
      setExpanded(null);
      setDetail(null);
      return;
    }
    setExpanded(id);
    try {
      const d = await getConversation(id);
      setDetail(d);
    } catch {
      setDetail(null);
    }
  }

  return (
    <div className="rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold text-foreground">Chat History</h2>
      <p className="mt-0.5 text-xs text-foreground-subtle">
        Matched by email — anonymous or differently-emailed chats won&apos;t appear here.
      </p>
      {chats.length === 0 ? (
        <p className="mt-2 text-sm text-foreground-muted">No chat conversations found.</p>
      ) : (
        <div className="mt-3 flex flex-col gap-2">
          {chats.map((c) => (
            <div key={c.id} className="rounded-md border border-border">
              <button
                onClick={() => toggle(c.id)}
                className="flex w-full items-center justify-between p-3 text-left transition-colors hover:bg-foreground/5"
              >
                <span className="text-sm text-foreground">
                  Conversation {c.id.slice(0, 8)} · {c.message_count} messages
                </span>
                <span className="text-xs text-foreground-subtle">
                  {new Date(c.created_at).toLocaleString()}
                </span>
              </button>
              {expanded === c.id && detail && (
                <div className="border-t border-border p-3 flex flex-col gap-2">
                  {detail.messages.map((m) => (
                    <div key={m.id} className="text-xs">
                      <span className="font-medium text-foreground capitalize">{m.sender_type}: </span>
                      <span className="text-foreground-muted">{m.body}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const TIMELINE_ICONS: Record<string, string> = {
  ticket_created: "🎫", chat_started: "💬", note_added: "📝", automation_triggered: "⚡", event: "•",
};

function TimelineSection({ items }: { items: TimelineItem[] }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold text-foreground">Timeline</h2>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-foreground-muted">No activity yet.</p>
      ) : (
        <div className="mt-3 flex flex-col gap-3">
          {items.map((item, i) => (
            <div key={i} className="flex items-start gap-2 text-xs">
              <span>{TIMELINE_ICONS[item.type] || "•"}</span>
              <div className="flex-1">
                <p className="text-foreground">{describeTimelineItem(item)}</p>
                <p className="text-foreground-subtle">{new Date(item.timestamp).toLocaleString()}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function describeTimelineItem(item: TimelineItem): string {
  const d = item.data;
  switch (item.type) {
    case "ticket_created":
      return `Ticket created: "${d.subject}"`;
    case "chat_started":
      return "Chat conversation started";
    case "note_added":
      return `Note added: "${d.excerpt}"`;
    case "automation_triggered":
      return `Automation triggered (${d.trigger_type})`;
    default:
      return "Event";
  }
}

function NotesSection({
  customerId, notes, onChange,
}: { customerId: string; notes: CustomerNote[]; onChange: () => void }) {
  const [newBody, setNewBody] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editBody, setEditBody] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newBody.trim()) return;
    setSubmitting(true);
    try {
      await createCustomerNote(customerId, newBody.trim());
      setNewBody("");
      onChange();
    } finally {
      setSubmitting(false);
    }
  }

  async function handleUpdate(noteId: string) {
    if (!editBody.trim()) return;
    await updateCustomerNote(customerId, noteId, editBody.trim());
    setEditingId(null);
    onChange();
  }

  async function handleDelete(noteId: string) {
    if (!confirm("Delete this note?")) return;
    await deleteCustomerNote(customerId, noteId);
    onChange();
  }

  return (
    <div className="rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold text-foreground">Internal Notes</h2>

      <form onSubmit={handleCreate} className="mt-3 flex flex-col gap-2">
        <textarea
          value={newBody}
          onChange={(e) => setNewBody(e.target.value)}
          rows={3}
          placeholder="Add a note..."
          className="rounded-md border border-border bg-transparent px-3 py-2 text-sm text-foreground transition-colors focus:border-primary outline-none"
        />
        <button
          type="submit"
          disabled={submitting || !newBody.trim()}
          className="self-end rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground disabled:opacity-50"
        >
          {submitting ? "Adding..." : "Add Note"}
        </button>
      </form>

      <div className="mt-4 flex flex-col gap-2">
        {notes.length === 0 && <p className="text-sm text-foreground-muted">No notes yet.</p>}
        {notes.map((n) => (
          <div key={n.id} className="rounded-md border border-border p-3">
            {editingId === n.id ? (
              <div className="flex flex-col gap-2">
                <textarea
                  value={editBody}
                  onChange={(e) => setEditBody(e.target.value)}
                  rows={3}
                  className="rounded-md border border-border bg-transparent px-2 py-1 text-xs text-foreground"
                />
                <div className="flex gap-2">
                  <button onClick={() => handleUpdate(n.id)} className="rounded-md border border-border px-2 py-1 text-xs hover:bg-foreground/5">Save</button>
                  <button onClick={() => setEditingId(null)} className="rounded-md border border-border px-2 py-1 text-xs hover:bg-foreground/5">Cancel</button>
                </div>
              </div>
            ) : (
              <>
                <p className="text-xs text-foreground">{n.body}</p>
                <div className="mt-2 flex items-center justify-between">
                  <p className="text-[10px] text-foreground-subtle">
                    {n.author_name || "Unknown"} · {new Date(n.created_at).toLocaleString()}
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => { setEditingId(n.id); setEditBody(n.body); }}
                      className="text-[10px] text-foreground-muted hover:text-foreground"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(n.id)}
                      className="text-[10px] text-red-500 hover:text-red-400"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}