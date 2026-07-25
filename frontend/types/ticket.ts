export type TicketStatus = "open" | "pending" | "on_hold" | "resolved" | "closed";
export type TicketPriority = "low" | "medium" | "high" | "urgent";
export type TicketSource = "web" | "customer_portal" | "email";
export type InboxView = "mine" | "unassigned" | "all";

export interface TicketComment {
  id: string;
  ticket_id: string;
  author_id: string;
  body: string;
  is_internal_note: boolean;
  created_at: string;
  is_email: boolean;
  email_status: "received" | "pending" | "sent" | "failed" | null;
  email_from: string | null;
}

export interface Ticket {
  id: string;
  subject: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  requester_name: string;
  requester_email: string;
  created_by: string;
  assigned_to: string | null;
  team_id: string | null;
  organization_id: string;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  unread: boolean;
  source: TicketSource;
  inbox_id: string | null;
  email_thread_id: string | null;
  replied: boolean;
}

export interface TicketDetail extends Ticket {
  comments: TicketComment[];
}

export interface TicketCreateInput {
  subject: string;
  description: string;
  priority: TicketPriority;
  requester_name: string;
  requester_email: string;
  assigned_to?: string | null;
  team_id?: string | null;
}

export interface TicketUpdateInput {
  subject?: string;
  description?: string;
  status?: TicketStatus;
  priority?: TicketPriority;
  assigned_to?: string | null;
  team_id?: string | null;
}

export interface TicketCommentCreateInput {
  body: string;
  is_internal_note?: boolean;
}

export interface TicketListFilters {
  view?: InboxView;
  status?: TicketStatus;
  priority?: TicketPriority;
  assigned_to?: string;
  search?: string;
  unread?: boolean;
  archived?: boolean;
  skip?: number;
  limit?: number;
}

export interface InboxCounts {
  mine: number;
  unassigned: number;
  all_open: number;
  unread: number;
}

export type InboxState = "all" | "unread" | "replied" | "pending" | "archived";