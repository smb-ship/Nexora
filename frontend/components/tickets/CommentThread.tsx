"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Lock } from "lucide-react";
import { addTicketComment } from "@/lib/api/tickets";
import type { TicketComment } from "@/types/ticket";

interface CommentThreadProps {
  ticketId: string;
  comments: TicketComment[];
  onCommentAdded: (comment: TicketComment) => void;
  draftText?: string | null;
  onDraftConsumed?: () => void;
}

export function CommentThread({
  ticketId,
  comments,
  onCommentAdded,
  draftText,
  onDraftConsumed,
}: CommentThreadProps) {
  const [body, setBody] = useState("");
  const [isInternal, setIsInternal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (draftText) {
      setBody(draftText);
      onDraftConsumed?.();
    }
  }, [draftText, onDraftConsumed]);

  async function handleSubmit() {
    if (!body.trim()) return;
    setSubmitting(true);
    try {
      const comment = await addTicketComment(ticketId, { body, is_internal_note: isInternal });
      onCommentAdded(comment);
      setBody("");
      setIsInternal(false);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Activity</h2>

      <div className="space-y-3">
        {comments.length === 0 && (
          <p className="text-sm text-muted-foreground">No activity yet.</p>
        )}
        {comments.map((comment) => (
          <div
            key={comment.id}
            className={`rounded-lg border p-3 text-sm ${
              comment.is_internal_note
                ? "border-amber-500/30 bg-amber-500/10"
                : "border-border bg-card"
            }`}
          >
            {comment.is_internal_note && (
              <div className="mb-1 flex items-center gap-1 text-xs font-medium text-amber-400">
                <Lock className="h-3 w-3" />
                Internal note
              </div>
            )}
            <p>{comment.body}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {new Date(comment.created_at).toLocaleString()}
            </p>
          </div>
        ))}
      </div>

      <div className="space-y-2 border-t border-border pt-4">
        <Textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Write a reply or note…"
          rows={3}
        />
        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <Checkbox checked={isInternal} onCheckedChange={(v) => setIsInternal(Boolean(v))} />
            Internal note (not visible to customer)
          </label>
          <Button onClick={handleSubmit} disabled={submitting || !body.trim()}>
            {submitting ? "Sending…" : "Send"}
          </Button>
        </div>
      </div>
    </div>
  );
}