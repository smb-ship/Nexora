"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  getConversation,
  sendAgentReply,
  convertToTicket,
  type ChatConversationDetail,
} from "@/services/chat";

export default function ChatConversationDetailPage() {
  const params = useParams<{ conversationId: string }>();
  const router = useRouter();
  const conversationId = params.conversationId;

  const [conversation, setConversation] = useState<ChatConversationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [replyBody, setReplyBody] = useState("");
  const [sending, setSending] = useState(false);
  const [converting, setConverting] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  function load() {
    getConversation(conversationId)
      .then(setConversation)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load conversation"));
  }

  useEffect(load, [conversationId]);

  // Full-conversation polling every 4s. No delta/since-X endpoint exists
  // on the backend (chat_staff.py always returns the full message list),
  // so this re-fetches everything each tick rather than diffing.
  useEffect(() => {
    const interval = setInterval(load, 4000);
    return () => clearInterval(interval);
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation?.messages.length]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!replyBody.trim()) return;
    setSending(true);
    try {
      await sendAgentReply(conversationId, replyBody.trim());
      setReplyBody("");
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to send reply");
    } finally {
      setSending(false);
    }
  }

  async function handleConvert() {
    if (!confirm("Convert this conversation to a ticket? This cannot be undone.")) return;
    setConverting(true);
    try {
      const result = await convertToTicket(conversationId);
      router.push(`/tickets/${result.ticket_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to convert to ticket");
      setConverting(false);
    }
  }

  if (error && !conversation) {
    return <p className="text-sm text-red-500">{error}</p>;
  }
  if (!conversation) {
    return <p className="text-sm text-foreground-muted">Loading...</p>;
  }

  const isConverted = conversation.status === "converted";

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <h1 className="text-lg font-semibold text-foreground">
            Conversation {conversation.id.slice(0, 8)}
          </h1>
          <p className="text-xs text-foreground-muted">Status: {conversation.status}</p>
        </div>
        {isConverted ? (
          <span className="rounded-md bg-blue-500/10 px-3 py-1.5 text-xs font-medium text-blue-500">
            Converted to ticket {conversation.ticket_id?.slice(0, 8)}
          </span>
        ) : (
          <button
            onClick={handleConvert}
            disabled={converting}
            className="rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-foreground/5 disabled:opacity-50"
          >
            {converting ? "Converting..." : "Convert to Ticket"}
          </button>
        )}
      </div>

      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}

      <div className="mt-4 flex-1 overflow-y-auto flex flex-col gap-3 pr-1">
        {conversation.messages.map((m) => (
          <div
            key={m.id}
            className={`max-w-[75%] rounded-lg px-3 py-2 text-sm ${
              m.sender_type === "agent"
                ? "self-end bg-foreground text-background"
                : m.sender_type === "visitor"
                ? "self-start bg-foreground/10 text-foreground"
                : "self-center bg-transparent text-xs text-foreground-subtle"
            }`}
          >
            <p>{m.body}</p>
            <p
              className={`mt-1 text-[10px] ${
                m.sender_type === "agent" ? "text-background/70" : "text-foreground-subtle"
              }`}
            >
              {m.sender_type} · {new Date(m.created_at).toLocaleTimeString()}
            </p>
          </div>
        ))}
        {conversation.messages.length === 0 && (
          <p className="text-sm text-foreground-muted">No messages yet.</p>
        )}
        <div ref={messagesEndRef} />
      </div>

      {!isConverted && (
        <form onSubmit={handleSend} className="mt-4 flex gap-2 border-t border-border pt-4">
          <input
            value={replyBody}
            onChange={(e) => setReplyBody(e.target.value)}
            placeholder="Type a reply..."
            className="flex-1 rounded-md border border-border bg-transparent px-3 py-2 text-sm text-foreground"
          />
          <button
            type="submit"
            disabled={sending || !replyBody.trim()}
            className="rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background disabled:opacity-50"
          >
            {sending ? "Sending..." : "Send"}
          </button>
        </form>
      )}
    </div>
  );
}