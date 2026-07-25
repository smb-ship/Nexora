export type WorkflowTriggerType =
  | "ticket_created"
  | "ticket_status_changed"
  | "ticket_priority_changed"
  | "ticket_assigned"
  | "ticket_unassigned"
  | "ticket_comment_added"
  | "ticket_sentiment_changed"
  | "ticket_idle";

export type WorkflowConditionField =
  | "status"
  | "priority"
  | "sentiment"
  | "team_id"
  | "assigned_to"
  | "is_unassigned"
  | "subject"
  | "description"
  | "hours_since_updated"
  | "hours_since_created";

export type WorkflowOperator =
  | "equals"
  | "not_equals"
  | "in"
  | "contains"
  | "greater_than"
  | "less_than"
  | "is_empty"
  | "is_not_empty";

export type WorkflowActionType =
  | "assign_team"
  | "assign_user"
  | "unassign"
  | "set_priority"
  | "set_status"
  | "add_internal_note";

export type ConditionLogic = "all" | "any";

export interface WorkflowCondition {
  id?: string;
  field: WorkflowConditionField;
  operator: WorkflowOperator;
  value: string | null;
  order: number;
}

export interface WorkflowAction {
  id?: string;
  action_type: WorkflowActionType;
  params: Record<string, string>;
  order: number;
}

export interface WorkflowRule {
  id: string;
  name: string;
  description: string | null;
  trigger_type: WorkflowTriggerType;
  condition_logic: ConditionLogic;
  is_active: boolean;
  run_order: number;
  created_by: string;
  created_at: string;
  updated_at: string;
  conditions: WorkflowCondition[];
  actions: WorkflowAction[];
}

export interface WorkflowRuleInput {
  name: string;
  description?: string | null;
  trigger_type: WorkflowTriggerType;
  condition_logic: ConditionLogic;
  is_active: boolean;
  run_order: number;
  conditions: WorkflowCondition[];
  actions: WorkflowAction[];
}

export interface WorkflowExecutionLog {
  id: string;
  rule_id: string;
  ticket_id: string;
  trigger_type: WorkflowTriggerType;
  success: boolean;
  error_message: string | null;
  actions_summary: { actions?: string[] };
  created_at: string;
}