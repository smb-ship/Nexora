"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listConversations, type ChatConversation } from "@/services/chat";

const STATUS_TABS = [
  { label: "Open", value: "open" },
  { label: "Converted", value: "converted" },
  { label: "Closed", value: "closed" },
  { label: "All", value: "" },
];

export default function ChatConversationsPage() {
  const [activeTab, setActiveTab] = useState("open");
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    listConversations(activeTab || undefined)
      .then(setConversations)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load conversations"))
      .finally(() => setLoading(false));
  }

  useEffect(load, [activeTab]);

  // Poll the list every 5s so new visitor conversations show up without
  // a manual refresh — same rationale as the detail page's polling.
  useEffect(() => {
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [activeTab]);

  return (
    <div className="flex flex-col gap-1">
      <div>
        <h1 className="text-xl font-semibold text-foreground tracking-tight">Live Chat</h1>
        <p className="text-sm text-foreground-muted">
          Website visitor conversations and agent replies.
        </p>
      </div>

      <div className="mt-4 flex gap-2 border-b border-border">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setActiveTab(tab.value)}
            className={`px-3 py-2 text-sm font-medium border-b-2 -mb-px ${
              activeTab === tab.value
                ? "border-foreground text-foreground"
                : "border-transparent text-foreground-muted hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error && <p className="mt-4 text-sm text-red-500">{error}</p>}
      {loading && conversations.length === 0 && (
        <p className="mt-4 text-sm text-foreground-muted">Loading...</p>
      )}

      <div className="mt-4 flex flex-col gap-2">
        {conversations.map((c) => (
          <Link
            key={c.id}
            href={`/chat/${c.id}`}
            className="flex items-center justify-between rounded-lg border border-border p-4 hover:bg-foreground/5"
          >
            <div>
              <p className="text-sm font-medium text-foreground">
                Conversation {c.id.slice(0, 8)}
                <span
                  className={`ml-2 rounded px-1.5 py-0.5 text-xs ${
                    c.status === "open"
                      ? "bg-green-500/10 text-green-500"
                      : c.status === "converted"
                      ? "bg-blue-500/10 text-blue-500"
                      : "bg-foreground/10 text-foreground-muted"
                  }`}
                >
                  {c.status}
                </span>
              </p>
              <p className="mt-0.5 text-xs text-foreground-muted">
                Updated {new Date(c.updated_at).toLocaleString()}
              </p>
            </div>
            {c.ticket_id && (
              <span className="text-xs text-foreground-subtle">
                → Ticket {c.ticket_id.slice(0, 8)}
              </span>
            )}
          </Link>
        ))}
        {conversations.length === 0 && !loading && (
          <p className="text-sm text-foreground-muted">No conversations in this view.</p>
        )}
      </div>
    </div>
  );
}