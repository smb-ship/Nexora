"use client";

import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { workflowsService } from "@/services/workflows";
import type { WorkflowRule, WorkflowRuleInput, WorkflowExecutionLog } from "@/types/workflow";
import { WorkflowRuleCard } from "@/components/workflows/WorkflowRuleCard";
import { WorkflowRuleModal } from "@/components/workflows/WorkflowRuleModal";

export default function WorkflowsPage() {
  const [rules, setRules] = useState<WorkflowRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<WorkflowRule | null>(null);
  const [logs, setLogs] = useState<WorkflowExecutionLog[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadRules = async () => {
    setLoading(true);
    try {
      setRules(await workflowsService.list());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workflow rules.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRules();
  }, []);

  const handleSave = async (payload: WorkflowRuleInput) => {
    if (editingRule) {
      await workflowsService.update(editingRule.id, payload);
    } else {
      await workflowsService.create(payload);
    }
    setModalOpen(false);
    setEditingRule(null);
    await loadRules();
  };

  const handleToggle = async (rule: WorkflowRule) => {
    await workflowsService.toggle(rule.id);
    await loadRules();
  };

  const handleDelete = async (rule: WorkflowRule) => {
    if (!confirm(`Delete rule "${rule.name}"? This cannot be undone.`)) return;
    await workflowsService.remove(rule.id);
    await loadRules();
  };

  const handleViewLogs = async (rule: WorkflowRule) => {
    setLogs(await workflowsService.logs(rule.id));
  };

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Workflow Automation</h1>
          <p className="text-sm text-slate-500">
            Automatically route, prioritize, and act on tickets based on triggers and conditions.
          </p>
        </div>
        <button
          onClick={() => { setEditingRule(null); setModalOpen(true); }}
          className="flex items-center gap-2 rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-500"
        >
          <Plus size={16} /> New rule
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-red-800 bg-red-950/50 px-3 py-2 text-sm text-red-300">{error}</div>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">Loading rules...</p>
      ) : rules.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-800 py-12 text-center text-sm text-slate-500">
          No workflow rules yet. Create one to start automating ticket handling.
        </div>
      ) : (
        <div className="space-y-2">
          {rules.map((rule) => (
            <WorkflowRuleCard
              key={rule.id}
              rule={rule}
              onToggle={handleToggle}
              onEdit={(r) => { setEditingRule(r); setModalOpen(true); }}
              onDelete={handleDelete}
              onViewLogs={handleViewLogs}
            />
          ))}
        </div>
      )}

      {modalOpen && (
        <WorkflowRuleModal
          initial={editingRule}
          onClose={() => { setModalOpen(false); setEditingRule(null); }}
          onSave={handleSave}
        />
      )}

      {logs && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setLogs(null)}>
          <div className="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-xl border border-slate-800 bg-slate-950 p-6" onClick={(e) => e.stopPropagation()}>
            <h2 className="mb-4 text-lg font-semibold text-slate-100">Run history</h2>
            {logs.length === 0 ? (
              <p className="text-sm text-slate-500">This rule hasn't run yet.</p>
            ) : (
              <div className="space-y-2">
                {logs.map((log) => (
                  <div key={log.id} className="rounded-md border border-slate-800 px-3 py-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className={log.success ? "text-emerald-400" : "text-red-400"}>
                        {log.success ? "Success" : "Failed"}
                      </span>
                      <span className="text-slate-500">{new Date(log.created_at).toLocaleString()}</span>
                    </div>
                    {log.success ? (
                      <p className="mt-1 text-slate-400">{log.actions_summary.actions?.join(", ")}</p>
                    ) : (
                      <p className="mt-1 text-red-300">{log.error_message}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}