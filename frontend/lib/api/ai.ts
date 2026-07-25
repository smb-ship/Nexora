import { apiFetch } from "@/lib/api/client";
import type { AIInsight, ReplySuggestionRequest, ReplySuggestionResponse } from "@/types/ai";

export async function getAIInsights(ticketId: string): Promise<AIInsight | null> {
  return apiFetch<AIInsight | null>(`/tickets/${ticketId}/ai/insights`);
}

export async function summarizeTicket(ticketId: string): Promise<AIInsight> {
  return apiFetch<AIInsight>(`/tickets/${ticketId}/ai/summarize`, { method: "POST" });
}

export async function analyzeSentiment(ticketId: string): Promise<AIInsight> {
  return apiFetch<AIInsight>(`/tickets/${ticketId}/ai/sentiment`, { method: "POST" });
}

export async function predictPriority(ticketId: string): Promise<AIInsight> {
  return apiFetch<AIInsight>(`/tickets/${ticketId}/ai/predict-priority`, { method: "POST" });
}

export async function suggestTags(ticketId: string): Promise<AIInsight> {
  return apiFetch<AIInsight>(`/tickets/${ticketId}/ai/suggest-tags`, { method: "POST" });
}

export async function suggestReply(
  ticketId: string,
  payload: ReplySuggestionRequest = {}
): Promise<ReplySuggestionResponse> {
  return apiFetch<ReplySuggestionResponse>(`/tickets/${ticketId}/ai/suggest-reply`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function generateInternalNote(ticketId: string): Promise<AIInsight> {
  return apiFetch<AIInsight>(`/tickets/${ticketId}/ai/internal-note`, { method: "POST" });
}