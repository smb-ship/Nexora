"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { InboxView, InboxCounts } from "@/types/ticket";

interface InboxTabsProps {
  active: InboxView;
  counts: InboxCounts | null;
  onChange: (view: InboxView) => void;
}

const TABS: { value: InboxView; label: string; countKey: keyof InboxCounts }[] = [
  { value: "mine", label: "Assigned to me", countKey: "mine" },
  { value: "unassigned", label: "Unassigned", countKey: "unassigned" },
  { value: "all", label: "All open", countKey: "all_open" },
];

export function InboxTabs({ active, counts, onChange }: InboxTabsProps) {
  return (
    <div data-slot="inbox-tabs" className="flex flex-col gap-0.5 p-2">
      {TABS.map((tab) => {
        const isActive = tab.value === active;
        const count = counts ? counts[tab.countKey] : undefined;
        return (
          <button
            key={tab.value}
            onClick={() => onChange(tab.value)}
            className={cn(
              "flex items-center justify-between rounded-md px-2.5 py-1.5 text-sm transition-colors",
              isActive
                ? "bg-accent text-accent-foreground"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <span>{tab.label}</span>
            {count !== undefined && count > 0 && (
              <Badge variant={isActive ? "default" : "secondary"}>{count}</Badge>
            )}
          </button>
        );
      })}
    </div>
  );
}