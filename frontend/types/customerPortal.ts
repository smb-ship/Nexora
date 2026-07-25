export type CustomerTicketStatus = "open" | "pending" | "on_hold" | "resolved" | "closed";
export type CustomerTicketPriority = "low" | "medium" | "high" | "urgent";
export type CustomerTicketCategory = "general" | "technical" | "billing" | "feature_request" | "other";

export interface CustomerAgentSummary {
  full_name: string | null;
}

export interface CustomerTicketListItem {
  id: string;
  subject: string;
  status: CustomerTicketStatus;
  priority: CustomerTicketPriority;
  category: CustomerTicketCategory;
  created_at: string;
  updated_at: string;
  assignee: CustomerAgentSummary | null;
}

export interface CustomerTicketDetail extends CustomerTicketListItem {
  description: string;
}

export interface CustomerTicketListResponse {
  items: CustomerTicketListItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface CustomerTicketCreateInput {
  subject: string;
  description: string;
  category: CustomerTicketCategory;
  priority: CustomerTicketPriority;
}

export interface CustomerComment {
  id: string;
  body: string;
  created_at: string;
  author_id: string;
  is_own_message: boolean;
}

export interface CustomerDashboardStats {
  total_tickets: number;
  open_tickets: number;
  resolved_tickets: number;
  closed_tickets: number;
  recent_tickets: CustomerTicketListItem[];
}