"use client";

import type { InboxState } from "@/types/ticket";

const STATES: { value: InboxState; label: string }[] = [
  { value: "all", label: "All" },
  { value: "unread", label: "Unread" },
  { value: "replied", label: "Replied" },
  { value: "pending", label: "Pending" },
  { value: "archived", label: "Archived" },
];

export function InboxStateFilters({
  value,
  onChange,
}: {
  value: InboxState;
  onChange: (state: InboxState) => void;
}) {
  return (
    <div className="flex gap-1 rounded-lg border border-border p-1">
      {STATES.map((s) => (
        <button
          key={s.value}
          onClick={() => onChange(s.value)}
          className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
            value === s.value
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted/50"
          }`}
        >
          {s.label}
        </button>
      ))}
    </div>
  );
}