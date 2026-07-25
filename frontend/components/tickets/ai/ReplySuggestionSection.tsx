"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { suggestReply } from "@/lib/api/ai";

interface ReplySuggestionSectionProps {
  ticketId: string;
  onUseReply?: (text: string) => void;
}

export function ReplySuggestionSection({ ticketId, onUseReply }: ReplySuggestionSectionProps) {
  const [instructions, setInstructions] = useState("");
  const [suggestion, setSuggestion] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const result = await suggestReply(ticketId, instructions ? { instructions } : {});
      setSuggestion(result.reply);
    } catch {
      setError("Couldn't generate a reply suggestion. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2">
      <h3 className="text-xs font-medium text-muted-foreground">Reply Suggestion</h3>

      <Textarea
        value={instructions}
        onChange={(e) => setInstructions(e.target.value)}
        placeholder="Optional: tell the AI what tone or points to include…"
        rows={2}
        className="text-sm"
      />

      <Button onClick={handleGenerate} disabled={loading} className="h-7 px-2 text-xs">
        {loading ? "Drafting…" : suggestion ? "Regenerate" : "Draft reply"}
      </Button>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {!error && suggestion && (
        <div className="space-y-2 rounded-md border border-border bg-card p-3">
          <p className="whitespace-pre-wrap text-sm">{suggestion}</p>
          {onUseReply && (
            <button onClick={() => onUseReply(suggestion)} className="text-xs text-purple-400 hover:underline">
              Use this reply
            </button>
          )}
        </div>
      )}

      <Separator />
    </div>
  );
}