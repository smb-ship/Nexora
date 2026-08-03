"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getArticle, updateArticle, deleteArticle, type KnowledgeArticle } from "@/services/knowledge";

export default function KnowledgeArticleDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [article, setArticle] = useState<KnowledgeArticle | null>(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [tagsInput, setTagsInput] = useState("");
  const [status, setStatus] = useState("draft");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getArticle(params.id)
      .then((a) => {
        setArticle(a);
        setTitle(a.title);
        setBody(a.body);
        setTagsInput(a.tags.join(", "));
        setStatus(a.status);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load article"));
  }, [params.id]);

  async function handleSave() {
    setSaving(true);
    try {
      const tags = tagsInput.split(",").map((t) => t.trim()).filter(Boolean);
      const updated = await updateArticle(params.id, { title, body, tags, status });
      setArticle(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to save article");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Delete this article? This cannot be undone.")) return;
    try {
      await deleteArticle(params.id);
      router.push("/knowledge");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to delete article");
    }
  }

  if (!article) {
    return error ? <p className="text-sm text-red-500">{error}</p> : <p className="text-sm text-foreground-muted">Loading...</p>;
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-foreground tracking-tight">Edit Article</h1>
        <div className="flex gap-2">
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="rounded-md border border-border bg-transparent px-2 py-1.5 text-sm text-foreground"
          >
            <option value="draft">Draft</option>
            <option value="published">Published</option>
          </select>
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save"}
          </button>
          <button
            onClick={handleDelete}
            className="rounded-md border border-border px-3 py-1.5 text-sm text-red-500 hover:bg-red-500/5"
          >
            Delete
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="rounded-md border border-border bg-transparent px-3 py-2 text-lg font-medium text-foreground"
        placeholder="Article title"
      />

      <input
        value={tagsInput}
        onChange={(e) => setTagsInput(e.target.value)}
        className="rounded-md border border-border bg-transparent px-3 py-1.5 text-sm text-foreground"
        placeholder="Tags, comma separated"
      />

      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        rows={16}
        className="rounded-md border border-border bg-transparent px-3 py-2 text-sm text-foreground font-mono"
        placeholder="Article body..."
      />

      <p className="text-xs text-foreground-subtle">
        {article.view_count} views · Updated {new Date(article.updated_at).toLocaleString()}
      </p>
    </div>
  );
}