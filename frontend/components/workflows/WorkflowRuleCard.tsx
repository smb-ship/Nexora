"use client";

import { Power, Pencil, Trash2, ScrollText } from "lucide-react";
import type { WorkflowRule } from "@/types/workflow";

const TRIGGER_LABELS: Record<string, string> = {
  ticket_created: "Ticket created",
  ticket_status_changed: "Status changed",
  ticket_priority_changed: "Priority changed",
  ticket_assigned: "Ticket assigned",
  ticket_unassigned: "Ticket unassigned",
  ticket_comment_added: "Reply added",
  ticket_sentiment_changed: "Sentiment changed",
  ticket_idle: "Ticket idle",
};

interface Props {
  rule: WorkflowRule;
  onToggle: (rule: WorkflowRule) => void;
  onEdit: (rule: WorkflowRule) => void;
  onDelete: (rule: WorkflowRule) => void;
  onViewLogs: (rule: WorkflowRule) => void;
}

export function WorkflowRuleCard({ rule, onToggle, onEdit, onDelete, onViewLogs }: Props) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${rule.is_active ? "bg-emerald-500" : "bg-slate-600"}`} />
          <h3 className="truncate text-sm font-medium text-slate-100">{rule.name}</h3>
        </div>
        <p className="mt-0.5 text-xs text-slate-500">
          {TRIGGER_LABELS[rule.trigger_type] ?? rule.trigger_type} &middot; {rule.conditions.length} condition
          {rule.conditions.length !== 1 ? "s" : ""} &middot; {rule.actions.length} action
          {rule.actions.length !== 1 ? "s" : ""}
        </p>
      </div>
      <div className="flex items-center gap-1">
        <button onClick={() => onViewLogs(rule)} className="rounded-md p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-200" title="View run history">
          <ScrollText size={16} />
        </button>
        <button onClick={() => onToggle(rule)} className="rounded-md p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-200" title={rule.is_active ? "Disable" : "Enable"}>
          <Power size={16} />
        </button>
        <button onClick={() => onEdit(rule)} className="rounded-md p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-200" title="Edit">
          <Pencil size={16} />
        </button>
        <button onClick={() => onDelete(rule)} className="rounded-md p-2 text-slate-400 hover:bg-slate-800 hover:text-red-400" title="Delete">
          <Trash2 size={16} />
        </button>
      </div>
    </div>
  );
}