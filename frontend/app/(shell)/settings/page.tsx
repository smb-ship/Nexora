"use client";

import { useEffect, useState } from "react";
import { getWidgetSettings, type ChatWidgetSettings } from "@/services/chat";

export default function SettingsPage() {
  const [widget, setWidget] = useState<ChatWidgetSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<"key" | "snippet" | null>(null);

  useEffect(() => {
    getWidgetSettings()
      .then(setWidget)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load widget settings"))
      .finally(() => setLoading(false));
  }, []);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  const embedSnippet = widget
    ? `<script src="${typeof window !== "undefined" ? window.location.origin : ""}/chat-widget.js"\n  data-public-key="${widget.public_key}"\n  data-api-base="${apiBase}"\n  async></script>`
    : "";

  function copy(text: string, which: "key" | "snippet") {
    navigator.clipboard.writeText(text);
    setCopied(which);
    setTimeout(() => setCopied(null), 1500);
  }

  return (
    <div className="flex flex-col gap-1">
      <div>
        <h1 className="text-xl font-semibold text-foreground tracking-tight">Settings</h1>
        <p className="text-sm text-foreground-muted">Account and workspace settings.</p>
      </div>

      {error && <p className="mt-4 text-sm text-red-500">{error}</p>}
      {loading && <p className="mt-4 text-sm text-foreground-muted">Loading...</p>}

      {widget && (
        <div className="mt-8">
          <h2 className="text-sm font-semibold text-foreground">Chat Widget</h2>
          <p className="mt-1 text-xs text-foreground-muted">
            Settings for the embeddable live chat widget. Currently read-only — editing
            the welcome message or active status requires a backend update endpoint that
            doesn&apos;t exist yet.
          </p>

          <div className="mt-4 flex flex-col gap-4 rounded-lg border border-border p-4">
            <div>
              <p className="text-xs font-medium text-foreground-muted">Status</p>
              <p className="mt-1 text-sm">
                <span
                  className={`rounded px-1.5 py-0.5 text-xs font-medium ${
                    widget.is_active ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"
                  }`}
                >
                  {widget.is_active ? "active" : "inactive"}
                </span>
              </p>
            </div>

            <div>
              <p className="text-xs font-medium text-foreground-muted">Welcome Message</p>
              <p className="mt-1 text-sm text-foreground">{widget.welcome_message}</p>
            </div>

            <div>
              <p className="text-xs font-medium text-foreground-muted">Public Key</p>
              <div className="mt-1 flex items-center gap-2">
                <code className="flex-1 truncate rounded bg-foreground/5 px-2 py-1 text-xs">
                  {widget.public_key}
                </code>
                <button
                  onClick={() => copy(widget.public_key, "key")}
                  className="rounded-md border border-border px-2 py-1 text-xs hover:bg-foreground/5"
                >
                  {copied === "key" ? "Copied" : "Copy"}
                </button>
              </div>
            </div>

            <div>
              <p className="text-xs font-medium text-foreground-muted">Embed Snippet</p>
              <p className="mt-0.5 text-xs text-foreground-subtle">
                Paste this before the closing &lt;/body&gt; tag on any site you want the
                chat widget to appear on.
              </p>
              <div className="mt-1 flex items-start gap-2">
                <pre className="flex-1 overflow-x-auto rounded bg-foreground/5 p-2 text-xs">
                  {embedSnippet}
                </pre>
                <button
                  onClick={() => copy(embedSnippet, "snippet")}
                  className="rounded-md border border-border px-2 py-1 text-xs hover:bg-foreground/5"
                >
                  {copied === "snippet" ? "Copied" : "Copy"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}