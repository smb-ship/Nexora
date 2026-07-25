"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Paperclip } from "lucide-react";
import { customerPortalService } from "@/services/customerPortal";
import type { CustomerTicketCategory, CustomerTicketPriority } from "@/types/customerPortal";

const CATEGORY_OPTIONS: { value: CustomerTicketCategory; label: string }[] = [
  { value: "general", label: "General" },
  { value: "technical", label: "Technical Issue" },
  { value: "billing", label: "Billing" },
  { value: "feature_request", label: "Feature Request" },
  { value: "other", label: "Other" },
];

const PRIORITY_OPTIONS: { value: CustomerTicketPriority; label: string }[] = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

export default function NewTicketPage() {
  const router = useRouter();
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<CustomerTicketCategory>("general");
  const [priority, setPriority] = useState<CustomerTicketPriority>("medium");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (subject.trim().length < 3) {
      setError("Subject must be at least 3 characters.");
      return;
    }
    if (description.trim().length < 10) {
      setError("Please provide a bit more detail (at least 10 characters).");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const ticket = await customerPortalService.createTicket({ subject, description, category, priority });
      router.push(`/portal/tickets/${ticket.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create ticket.");
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-1 text-xl font-semibold text-foreground">New Support Ticket</h1>
      <p className="mb-6 text-sm text-foreground-muted">
        Tell us what's going on and our team will get back to you.
      </p>

      {error && (
        <div className="mb-4 rounded-md border border-red-800 bg-red-950/50 px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm text-foreground-muted">Subject</label>
          <input
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Brief summary of your issue"
            className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground placeholder:text-foreground-muted"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm text-foreground-muted">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as CustomerTicketCategory)}
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground"
            >
              {CATEGORY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm text-foreground-muted">Priority</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as CustomerTicketPriority)}
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground"
            >
              {PRIORITY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm text-foreground-muted">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={6}
            placeholder="Please include as much detail as possible..."
            className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground placeholder:text-foreground-muted"
          />
        </div>

        <div className="rounded-md border border-dashed border-border px-4 py-6 text-center">
          <Paperclip className="mx-auto h-5 w-5 text-foreground-muted" />
          <p className="mt-2 text-sm text-foreground-muted">File attachments coming soon</p>
        </div>

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={() => router.back()}
            className="rounded-md border border-border px-4 py-2 text-sm text-foreground-muted hover:bg-surface-elevated"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            {submitting ? "Submitting..." : "Submit Ticket"}
          </button>
        </div>
      </form>
    </div>
  );
}