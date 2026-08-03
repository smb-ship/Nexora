"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listArticles, createArticle, type KnowledgeArticleListItem } from "@/services/knowledge";

export default function KnowledgePage() {
  const [articles, setArticles] = useState<KnowledgeArticleListItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");

  function load() {
    setLoading(true);
    listArticles(search ? { search } : undefined)
      .then(setArticles)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load articles"))
      .finally(() => setLoading(false));
  }

  useEffect(load, [search]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newTitle.trim()) return;
    setCreating(true);
    try {
      const article = await createArticle({ title: newTitle.trim(), body: "", tags: [], status: "draft" });
      window.location.href = `/knowledge/${article.id}`;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create article");
      setCreating(false);
    }
  }

  return (
    <div className="flex flex-col gap-1">
      <div>
        <h1 className="text-xl font-semibold text-foreground tracking-tight">Knowledge Hub</h1>
        <p className="text-sm text-foreground-muted">Articles and documentation.</p>
      </div>

      <div className="mt-4 flex gap-2">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search articles..."
          className="flex-1 rounded-md border border-border bg-transparent px-3 py-1.5 text-sm text-foreground"
        />
      </div>

      <form onSubmit={handleCreate} className="mt-4 flex gap-2">
        <input
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="New article title..."
          className="flex-1 rounded-md border border-border bg-transparent px-3 py-1.5 text-sm text-foreground"
        />
        <button
          type="submit"
          disabled={creating || !newTitle.trim()}
          className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background disabled:opacity-50"
        >
          {creating ? "Creating..." : "New Article"}
        </button>
      </form>

      {error && <p className="mt-4 text-sm text-red-500">{error}</p>}
      {loading && <p className="mt-4 text-sm text-foreground-muted">Loading...</p>}

      <div className="mt-4 flex flex-col gap-2">
        {articles.map((a) => (
          <Link
            key={a.id}
            href={`/knowledge/${a.id}`}
            className="flex items-center justify-between rounded-lg border border-border p-4 hover:bg-foreground/5"
          >
            <div>
              <p className="text-sm font-medium text-foreground">
                {a.title}
                <span
                  className={`ml-2 rounded px-1.5 py-0.5 text-xs ${
                    a.status === "published" ? "bg-green-500/10 text-green-500" : "bg-foreground/10 text-foreground-muted"
                  }`}
                >
                  {a.status}
                </span>
              </p>
              <p className="mt-0.5 text-xs text-foreground-muted">
                {a.tags.join(", ") || "no tags"} · {a.view_count} views
              </p>
            </div>
            <span className="text-xs text-foreground-subtle">
              {new Date(a.updated_at).toLocaleDateString()}
            </span>
          </Link>
        ))}
        {articles.length === 0 && !loading && (
          <p className="text-sm text-foreground-muted">No articles yet.</p>
        )}
      </div>
    </div>
  );
}