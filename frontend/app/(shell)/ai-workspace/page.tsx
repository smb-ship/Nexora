"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sparkles, BookOpen, Send, Trash2 } from "lucide-react";
import {
  askKnowledgeBase, listPrompts, createPrompt, deletePrompt, listRecentInsights,
  type RAGQueryResponse, type PromptTemplate, type TicketInsightSummary,
} from "@/services/aiWorkspace";

type Tab = "assistant" | "prompts" | "insights";

export default function AiWorkspacePage() {
  const [tab, setTab] = useState<Tab>("assistant");

  return (
    <div className="flex flex-col gap-1">
      <div>
        <h1 className="text-xl font-semibold text-foreground tracking-tight">AI Workspace</h1>
        <p className="text-sm text-foreground-muted">RAG-powered assistant, prompt library, and conversation insights.</p>
      </div>

      <div className="mt-4 flex gap-2 border-b border-border">
        {(["assistant", "prompts", "insights"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-2 text-sm font-medium border-b-2 -mb-px capitalize ${
              tab === t ? "border-foreground text-foreground" : "border-transparent text-foreground-muted hover:text-foreground"
            }`}
          >
            {t === "assistant" ? "Chat Assistant" : t}
          </button>
        ))}
      </div>

      <div className="mt-4">
        {tab === "assistant" && <ChatAssistantTab />}
        {tab === "prompts" && <PromptLibraryTab />}
        {tab === "insights" && <InsightsTab />}
      </div>
    </div>
  );
}

// --- Chat Assistant (RAG) ---

interface ChatTurn {
  question: string;
  response: RAGQueryResponse | null;
  error: string | null;
}

function ChatAssistantTab() {
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [asking, setAsking] = useState(false);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || asking) return;
    const q = question.trim();
    setQuestion("");
    setAsking(true);
    setTurns((prev) => [...prev, { question: q, response: null, error: null }]);
    try {
      const response = await askKnowledgeBase(q);
      setTurns((prev) => prev.map((t, i) => (i === prev.length - 1 ? { ...t, response } : t)));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to get an answer";
      setTurns((prev) => prev.map((t, i) => (i === prev.length - 1 ? { ...t, error: msg } : t)));
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-4 rounded-lg border border-border p-4 min-h-[300px]">
        {turns.length === 0 && (
          <p className="text-sm text-foreground-muted">
            Ask a question and I&apos;ll search your published Knowledge Base articles for an answer.
          </p>
        )}
        {turns.map((t, i) => (
          <div key={i} className="flex flex-col gap-2">
            <div className="self-end max-w-[80%] rounded-lg bg-foreground px-3 py-2 text-sm text-background">
              {t.question}
            </div>
            {t.error && <p className="text-sm text-red-500">{t.error}</p>}
            {!t.error && !t.response && (
              <div className="flex items-center gap-2 text-sm text-foreground-muted">
                <Sparkles className="h-3 w-3 animate-pulse" /> Thinking...
              </div>
            )}
            {t.response && (
              <div className="max-w-[85%] rounded-lg bg-foreground/5 px-3 py-2 text-sm text-foreground">
                <p>{t.response.answer}</p>
                {t.response.cited_articles.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {t.response.cited_articles.map((a) => (
                      <Link
                        key={a.id}
                        href={`/knowledge/${a.id}`}
                        className="flex items-center gap-1 rounded border border-border px-1.5 py-0.5 text-[10px] text-foreground-muted hover:bg-foreground/5"
                      >
                        <BookOpen className="h-2.5 w-2.5" /> {a.title} · {Math.round(a.similarity * 100)}%
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleAsk} className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about anything in your Knowledge Base..."
          className="flex-1 rounded-md border border-border bg-transparent px-3 py-2 text-sm text-foreground"
        />
        <button
          type="submit"
          disabled={asking || !question.trim()}
          className="flex items-center gap-1 rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background disabled:opacity-50"
        >
          <Send className="h-3.5 w-3.5" /> Ask
        </button>
      </form>
    </div>
  );
}

// --- Prompt Library ---

function PromptLibraryTab() {
  const [prompts, setPrompts] = useState<PromptTemplate[]>([]);
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  function load() {
    listPrompts().then(setPrompts).finally(() => setLoading(false));
  }
  useEffect(load, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !text.trim()) return;
    setSubmitting(true);
    try {
      await createPrompt(title.trim(), text.trim());
      setTitle(""); setText("");
      load();
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    await deletePrompt(id);
    load();
  }

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={handleCreate} className="flex flex-col gap-2 rounded-lg border border-border p-4">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Prompt title (e.g. 'Refund apology')"
          className="rounded-md border border-border bg-transparent px-3 py-1.5 text-sm text-foreground"
        />
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          placeholder="The prompt text..."
          className="rounded-md border border-border bg-transparent px-3 py-2 text-sm text-foreground"
        />
        <button
          type="submit"
          disabled={submitting || !title.trim() || !text.trim()}
          className="self-end rounded-md bg-foreground px-3 py-1.5 text-xs font-medium text-background disabled:opacity-50"
        >
          {submitting ? "Saving..." : "Save Prompt"}
        </button>
      </form>

      {loading && <p className="text-sm text-foreground-muted">Loading...</p>}
      <div className="flex flex-col gap-2">
        {prompts.length === 0 && !loading && <p className="text-sm text-foreground-muted">No saved prompts yet.</p>}
        {prompts.map((p) => (
          <div key={p.id} className="rounded-lg border border-border p-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-foreground">{p.title}</p>
              <button onClick={() => handleDelete(p.id)} className="text-foreground-subtle hover:text-red-500">
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <p className="mt-1 text-xs text-foreground-muted">{p.prompt_text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Conversation Insights ---

function InsightsTab() {
  const [insights, setInsights] = useState<TicketInsightSummary[] | null>(null);

  useEffect(() => {
    listRecentInsights().then(setInsights);
  }, []);

  return (
    <div className="flex flex-col gap-2">
      {insights === null && <p className="text-sm text-foreground-muted">Loading...</p>}
      {insights?.length === 0 && <p className="text-sm text-foreground-muted">No AI insights generated yet.</p>}
      {insights?.map((i) => (
        <Link
          key={i.ticket_id}
          href={`/tickets/${i.ticket_id}`}
          className="rounded-lg border border-border p-3 hover:bg-foreground/5"
        >
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-foreground">{i.ticket_subject}</p>
            <span className="text-[10px] text-foreground-subtle">{new Date(i.generated_at).toLocaleDateString()}</span>
          </div>
          {i.summary && <p className="mt-1 text-xs text-foreground-muted">{i.summary}</p>}
          <div className="mt-2 flex flex-wrap gap-1.5">
            {i.sentiment && <span className="rounded bg-foreground/10 px-1.5 py-0.5 text-[10px] text-foreground-muted">{i.sentiment}</span>}
            {i.predicted_priority && <span className="rounded bg-foreground/10 px-1.5 py-0.5 text-[10px] text-foreground-muted">{i.predicted_priority}</span>}
            {i.suggested_tags.map((tag) => (
              <span key={tag} className="rounded bg-foreground/10 px-1.5 py-0.5 text-[10px] text-foreground-muted">{tag}</span>
            ))}
          </div>
        </Link>
      ))}
    </div>
  );
}