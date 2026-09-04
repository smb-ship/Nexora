import enum


class ToolRisk(str, enum.Enum):
    """Execution risk tier for a Support Operations Agent tool.

    READ tools may run automatically - they only read data the calling
    staff user could already see through the normal UI. No approval gate.

    WRITE tools mutate data but are routine, reversible support actions
    (change priority, assign, add an internal note). Milestone 3 will
    require the calling staff user to hold the matching Permission
    (app.core.permissions) for the underlying action - the agent never
    gets authority the human it's acting for doesn't have.

    HIGH_RISK tools are irreversible or customer-visible (sending a
    reply, closing a ticket, triggering a workflow). Per the product
    spec these must never execute on the agent's own authority. Until
    Milestone 5 (human-in-the-loop approvals) exists, every HIGH_RISK
    tool's executor refuses to run and returns an explanatory
    ToolResult instead of touching the database - see the executors in
    app/agent/tools/*.py. The tool is still registered (so the model
    can see the capability exists and the future Milestone 12 tool UI
    can list it as "Approval Required"), it just can't act yet.
    """

    READ = "read"
    WRITE = "write"
    HIGH_RISK = "high_risk"