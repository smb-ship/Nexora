const STATUS_STYLES: Record<string, string> = {
  open: "bg-blue-500/10 text-blue-400",
  pending: "bg-amber-500/10 text-amber-400",
  on_hold: "bg-slate-500/10 text-slate-400",
  resolved: "bg-emerald-500/10 text-emerald-400",
  closed: "bg-slate-500/10 text-slate-500",
};

const STATUS_LABELS: Record<string, string> = {
  open: "Open",
  pending: "Pending",
  on_hold: "On Hold",
  resolved: "Resolved",
  closed: "Closed",
};

const PRIORITY_STYLES: Record<string, string> = {
  low: "bg-slate-500/10 text-slate-400",
  medium: "bg-blue-500/10 text-blue-400",
  high: "bg-amber-500/10 text-amber-400",
  urgent: "bg-red-500/10 text-red-400",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[status] ?? STATUS_STYLES.open}`}>
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}

export function PriorityBadge({ priority }: { priority: string }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${PRIORITY_STYLES[priority] ?? PRIORITY_STYLES.medium}`}>
      {priority}
    </span>
  );
}