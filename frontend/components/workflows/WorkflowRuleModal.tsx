"use client";

import { useState } from "react";
import { X, Plus, Trash2 } from "lucide-react";
import type {
  WorkflowRule,
  WorkflowRuleInput,
  WorkflowCondition,
  WorkflowAction,
  WorkflowTriggerType,
  WorkflowConditionField,
  WorkflowOperator,
  WorkflowActionType,
  ConditionLogic,
} from "@/types/workflow";

const TRIGGER_OPTIONS: { value: WorkflowTriggerType; label: string }[] = [
  { value: "ticket_created", label: "Ticket is created" },
  { value: "ticket_status_changed", label: "Ticket status changes" },
  { value: "ticket_priority_changed", label: "Ticket priority changes" },
  { value: "ticket_assigned", label: "Ticket is assigned" },
  { value: "ticket_unassigned", label: "Ticket is unassigned" },
  { value: "ticket_comment_added", label: "A reply is added" },
  { value: "ticket_sentiment_changed", label: "AI sentiment changes" },
  { value: "ticket_idle", label: "Ticket has been idle" },
];

const FIELD_OPTIONS: { value: WorkflowConditionField; label: string }[] = [
  { value: "status", label: "Status" },
  { value: "priority", label: "Priority" },
  { value: "sentiment", label: "AI Sentiment" },
  { value: "team_id", label: "Team" },
  { value: "assigned_to", label: "Assigned user" },
  { value: "is_unassigned", label: "Is unassigned" },
  { value: "subject", label: "Subject" },
  { value: "description", label: "Description" },
  { value: "hours_since_updated", label: "Hours since last update" },
  { value: "hours_since_created", label: "Hours since created" },
];

const OPERATOR_OPTIONS: { value: WorkflowOperator; label: string }[] = [
  { value: "equals", label: "equals" },
  { value: "not_equals", label: "does not equal" },
  { value: "in", label: "is one of (comma separated)" },
  { value: "contains", label: "contains" },
  { value: "greater_than", label: "is greater than" },
  { value: "less_than", label: "is less than" },
  { value: "is_empty", label: "is empty" },
  { value: "is_not_empty", label: "is not empty" },
];

const ACTION_OPTIONS: { value: WorkflowActionType; label: string }[] = [
  { value: "assign_team", label: "Assign to team" },
  { value: "assign_user", label: "Assign to user" },
  { value: "unassign", label: "Unassign ticket" },
  { value: "set_priority", label: "Set priority" },
  { value: "set_status", label: "Set status" },
  { value: "add_internal_note", label: "Add internal note" },
];

function emptyCondition(): WorkflowCondition {
  return { field: "status", operator: "equals", value: "", order: 0 };
}

function emptyAction(): WorkflowAction {
  return { action_type: "assign_team", params: {}, order: 0 };
}

interface Props {
  initial?: WorkflowRule | null;
  onClose: () => void;
  onSave: (payload: WorkflowRuleInput) => Promise<void>;
}

export function WorkflowRuleModal({ initial, onClose, onSave }: Props) {
  const [name, setName] = useState(initial?.name ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [triggerType, setTriggerType] = useState<WorkflowTriggerType>(initial?.trigger_type ?? "ticket_created");
  const [conditionLogic, setConditionLogic] = useState<ConditionLogic>(initial?.condition_logic ?? "all");
  const [isActive, setIsActive] = useState(initial?.is_active ?? true);
  const [conditions, setConditions] = useState<WorkflowCondition[]>(initial?.conditions ?? []);
  const [actions, setActions] = useState<WorkflowAction[]>(initial?.actions ?? [emptyAction()]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateCondition = (index: number, patch: Partial<WorkflowCondition>) => {
    setConditions((prev) => prev.map((c, i) => (i === index ? { ...c, ...patch } : c)));
  };

  const updateAction = (index: number, patch: Partial<WorkflowAction>) => {
    setActions((prev) => prev.map((a, i) => (i === index ? { ...a, ...patch } : a)));
  };

  const updateActionParam = (index: number, key: string, value: string) => {
    setActions((prev) => prev.map((a, i) => (i === index ? { ...a, params: { ...a.params, [key]: value } } : a)));
  };

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError("Rule name is required.");
      return;
    }
    if (actions.length === 0) {
      setError("At least one action is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSave({
        name,
        description: description || null,
        trigger_type: triggerType,
        condition_logic: conditionLogic,
        is_active: isActive,
        run_order: initial?.run_order ?? 0,
        conditions: conditions.map((c, i) => ({ ...c, order: i })),
        actions: actions.map((a, i) => ({ ...a, order: i })),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save rule.");
    } finally {
      setSaving(false);
    }
  };

  const renderActionParams = (action: WorkflowAction, index: number) => {
    switch (action.action_type) {
      case "assign_team":
        return (
          <input
            className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100"
            placeholder="Team ID"
            value={action.params.team_id ?? ""}
            onChange={(e) => updateActionParam(index, "team_id", e.target.value)}
          />
        );
      case "assign_user":
        return (
          <input
            className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100"
            placeholder="User ID"
            value={action.params.user_id ?? ""}
            onChange={(e) => updateActionParam(index, "user_id", e.target.value)}
          />
        );
      case "set_priority":
        return (
          <select
            className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100"
            value={action.params.priority ?? "low"}
            onChange={(e) => updateActionParam(index, "priority", e.target.value)}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
        );
      case "set_status":
        return (
          <select
            className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100"
            value={action.params.status ?? "open"}
            onChange={(e) => updateActionParam(index, "status", e.target.value)}
          >
            <option value="open">Open</option>
            <option value="pending">Pending</option>
            <option value="on_hold">On hold</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        );
      case "add_internal_note":
        return (
          <input
            className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100"
            placeholder="Note text"
            value={action.params.message ?? ""}
            onChange={(e) => updateActionParam(index, "message", e.target.value)}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-slate-800 bg-slate-950 p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-100">
            {initial ? "Edit workflow rule" : "New workflow rule"}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-md border border-red-800 bg-red-950/50 px-3 py-2 text-sm text-red-300">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-sm text-slate-400">Name</label>
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Escalate negative sentiment"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm text-slate-400">Description (optional)</label>
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              value={description ?? ""}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-sm text-slate-400">Trigger</label>
              <select
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                value={triggerType}
                onChange={(e) => setTriggerType(e.target.value as WorkflowTriggerType)}
              >
                {TRIGGER_OPTIONS.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div className="flex items-end gap-2">
              <input
                id="is_active"
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="h-4 w-4"
              />
              <label htmlFor="is_active" className="text-sm text-slate-300">Rule is active</label>
            </div>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-sm text-slate-400">
                Conditions ({conditionLogic === "all" ? "match ALL" : "match ANY"})
              </label>
              <div className="flex items-center gap-2">
                <select
                  className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-100"
                  value={conditionLogic}
                  onChange={(e) => setConditionLogic(e.target.value as ConditionLogic)}
                >
                  <option value="all">Match ALL</option>
                  <option value="any">Match ANY</option>
                </select>
                <button
                  type="button"
                  onClick={() => setConditions((prev) => [...prev, emptyCondition()])}
                  className="flex items-center gap-1 rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-300 hover:bg-slate-800"
                >
                  <Plus size={14} /> Add condition
                </button>
              </div>
            </div>

            {conditions.length === 0 && (
              <p className="text-xs text-slate-500">No conditions — this rule runs on every matching trigger.</p>
            )}

            <div className="space-y-2">
              {conditions.map((c, i) => (
                <div key={i} className="flex items-center gap-2">
                  <select
                    className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm text-slate-100"
                    value={c.field}
                    onChange={(e) => updateCondition(i, { field: e.target.value as WorkflowConditionField })}
                  >
                    {FIELD_OPTIONS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
                  </select>
                  <select
                    className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm text-slate-100"
                    value={c.operator}
                    onChange={(e) => updateCondition(i, { operator: e.target.value as WorkflowOperator })}
                  >
                    {OPERATOR_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                  {c.operator !== "is_empty" && c.operator !== "is_not_empty" && (
                    <input
                      className="flex-1 rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm text-slate-100"
                      placeholder="Value"
                      value={c.value ?? ""}
                      onChange={(e) => updateCondition(i, { value: e.target.value })}
                    />
                  )}
                  <button
                    type="button"
                    onClick={() => setConditions((prev) => prev.filter((_, idx) => idx !== i))}
                    className="text-slate-500 hover:text-red-400"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-sm text-slate-400">Actions</label>
              <button
                type="button"
                onClick={() => setActions((prev) => [...prev, emptyAction()])}
                className="flex items-center gap-1 rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-300 hover:bg-slate-800"
              >
                <Plus size={14} /> Add action
              </button>
            </div>

            <div className="space-y-2">
              {actions.map((a, i) => (
                <div key={i} className="flex items-center gap-2">
                  <select
                    className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm text-slate-100"
                    value={a.action_type}
                    onChange={(e) => updateAction(i, { action_type: e.target.value as WorkflowActionType, params: {} })}
                  >
                    {ACTION_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                  <div className="flex-1">{renderActionParams(a, i)}</div>
                  <button
                    type="button"
                    onClick={() => setActions((prev) => prev.filter((_, idx) => idx !== i))}
                    className="text-slate-500 hover:text-red-400"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-500 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save rule"}
          </button>
        </div>
      </div>
    </div>
  );
}