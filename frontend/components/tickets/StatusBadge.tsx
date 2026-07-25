import { Badge } from "@/components/ui/badge";
import type { TicketStatus } from "@/types/ticket";

const STATUS_STYLES: Record<TicketStatus, string> = {
  open: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  pending: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  on_hold: "bg-slate-500/15 text-slate-400 border-slate-500/30",
  resolved: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  closed: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
};

const STATUS_LABELS: Record<TicketStatus, string> = {
  open: "Open",
  pending: "Pending",
  on_hold: "On Hold",
  resolved: "Resolved",
  closed: "Closed",
};

export function StatusBadge({ status }: { status: TicketStatus }) {
  return (
    <Badge variant="outline" className={STATUS_STYLES[status]}>
      {STATUS_LABELS[status]}
    </Badge>
  );
}