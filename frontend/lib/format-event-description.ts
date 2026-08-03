import type { RecentEvent } from "@/services/dashboard";

const EVENT_LABELS: Record<string, string> = {
  ticket_created: "Ticket created",
  ticket_status_changed: "Ticket status changed",
  ticket_priority_changed: "Ticket priority changed",
  ticket_assigned: "Ticket assigned",
  ticket_unassigned: "Ticket unassigned",
  ticket_comment_added: "Comment added",
  ticket_sentiment_changed: "Sentiment changed",
  ticket_idle: "Ticket marked idle",
  email_received: "Email received",
  email_sent: "Email sent",
  ai_completed: "AI analysis completed",
  customer_created: "Customer created",
  workflow_executed: "Workflow executed",
};

export function formatEventDescription(event: RecentEvent): string {
  const label = EVENT_LABELS[event.event_type] || event.event_type;
  const data = event.data || {};

  if (event.event_type === "ticket_created" && typeof data.subject === "string") {
    return `${label}: "${data.subject}"`;
  }
  if (event.event_type === "ticket_comment_added" && data.source === "chat_conversion") {
    return "Chat conversation converted to ticket";
  }
  if (event.event_type === "ai_completed" && typeof data.sentiment === "string") {
    return `${label} — sentiment: ${data.sentiment}`;
  }
  return label;
}