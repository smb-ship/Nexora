import enum


class WorkflowTriggerType(str, enum.Enum):
    TICKET_CREATED = "ticket_created"
    TICKET_STATUS_CHANGED = "ticket_status_changed"
    TICKET_PRIORITY_CHANGED = "ticket_priority_changed"
    TICKET_ASSIGNED = "ticket_assigned"
    TICKET_UNASSIGNED = "ticket_unassigned"
    TICKET_COMMENT_ADDED = "ticket_comment_added"
    TICKET_SENTIMENT_CHANGED = "ticket_sentiment_changed"
    TICKET_IDLE = "ticket_idle"


class WorkflowConditionField(str, enum.Enum):
    STATUS = "status"
    PRIORITY = "priority"
    SENTIMENT = "sentiment"
    TEAM_ID = "team_id"
    ASSIGNED_TO = "assigned_to"
    IS_UNASSIGNED = "is_unassigned"
    SUBJECT = "subject"
    DESCRIPTION = "description"
    HOURS_SINCE_UPDATED = "hours_since_updated"
    HOURS_SINCE_CREATED = "hours_since_created"


class WorkflowOperator(str, enum.Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    CONTAINS = "contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


class WorkflowActionType(str, enum.Enum):
    ASSIGN_TEAM = "assign_team"
    ASSIGN_USER = "assign_user"
    UNASSIGN = "unassign"
    SET_PRIORITY = "set_priority"
    SET_STATUS = "set_status"
    ADD_INTERNAL_NOTE = "add_internal_note"


class ConditionLogic(str, enum.Enum):
    ALL = "all"
    ANY = "any"