"use client";

import { useEffect, useState, use as usePromise } from "react";
import Link from "next/link";
import { ArrowLeft, Send } from "lucide-react";
import { customerPortalService } from "@/services/customerPortal";
import type { CustomerTicketDetail, CustomerComment } from "@/types/customerPortal";
import { StatusBadge, PriorityBadge } from "@/components/customer-portal/Badges";

export default function TicketDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = usePromise(params);

  const [ticket, setTicket] = useState<CustomerTicketDetail | null>(null);
  const [comments, setComments] = useState<CustomerComment[]>([]);
  const [loading, setLoading] = useState(true);
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [t, c] = await Promise.all([
        customerPortalService.getTicket(id),
        customerPortalService.listComments(id),
      ]);
      setTicket(t);
      setComments(c);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load ticket.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reply.trim()) return;
    setSending(true);
    try {
      const comment = await customerPortalService.addComment(id, reply);
      setComments((prev) => [...prev, comment]);
      setReply("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send reply.");
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return <p className="mx-auto max-w-3xl text-sm text-foreground-muted">Loading...</p>;
  }

  if (error || !ticket) {
    return (
      <div className="mx-auto max-w-3xl">
        <p className="text-sm text-red-400">{error ?? "Ticket not found."}</p>
        <Link href="/portal/tickets" className="mt-2 inline-block text-sm text-primary hover:underline">
          Back to My Tickets
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Link href="/portal/tickets" className="flex items-center gap-1 text-sm text-foreground-muted hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to My Tickets
      </Link>

      <div className="rounded-lg border border-border bg-surface p-5">
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-lg font-semibold text-foreground">{ticket.subject}</h1>
          <div className="flex shrink-0 gap-2">
            <PriorityBadge priority={ticket.priority} />
            <StatusBadge status={ticket.status} />
          </div>
        </div>
        <p className="mt-3 whitespace-pre-wrap text-sm text-foreground-muted">{ticket.description}</p>

        <div className="mt-4 grid grid-cols-2 gap-3 border-t border-border-subtle pt-4 text-xs text-foreground-muted sm:grid-cols-4">
          <div>
            <p className="text-foreground-muted">Category</p>
            <p className="mt-0.5 capitalize text-foreground">{ticket.category.replace("_", " ")}</p>
          </div>
          <div>
            <p className="text-foreground-muted">Assigned Agent</p>
            <p className="mt-0.5 text-foreground">{ticket.assignee?.full_name ?? "Unassigned"}</p>
          </div>
          <div>
            <p className="text-foreground-muted">Created</p>
            <p className="mt-0.5 text-foreground">{new Date(ticket.created_at).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-foreground-muted">Last Updated</p>
            <p className="mt-0.5 text-foreground">{new Date(ticket.updated_at).toLocaleString()}</p>
          </div>
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-medium text-foreground">Conversation</h2>
        <div className="space-y-3">
          {comments.length === 0 && (
            <p className="text-sm text-foreground-muted">No replies yet.</p>
          )}
          {comments.map((c) => (
            <div
              key={c.id}
              className={`max-w-[85%] rounded-lg border px-4 py-3 text-sm ${
                c.is_own_message
                  ? "ml-auto border-primary/30 bg-primary/10 text-foreground"
                  : "border-border bg-surface text-foreground"
              }`}
            >
              <p className="whitespace-pre-wrap">{c.body}</p>
              <p className="mt-1.5 text-xs text-foreground-muted">
                {c.is_own_message ? "You" : "Support Team"} &middot; {new Date(c.created_at).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-red-800 bg-red-950/50 px-3 py-2 text-sm text-red-300">{error}</div>
      )}

      <form onSubmit={handleReply} className="flex gap-2">
        <input
          value={reply}
          onChange={(e) => setReply(e.target.value)}
          placeholder="Type a reply..."
          className="flex-1 rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground placeholder:text-foreground-muted"
        />
        <button
          type="submit"
          disabled={sending || !reply.trim()}
          className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          <Send className="h-4 w-4" /> Send
        </button>
      </form>
    </div>
  );
}