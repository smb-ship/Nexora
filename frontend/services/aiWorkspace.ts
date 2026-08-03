const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Request failed (${res.status}): ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface CitedArticle {
  id: string;
  title: string;
  similarity: number;
}

export interface RAGQueryResponse {
  answer: string;
  cited_articles: CitedArticle[];
}

export interface PromptTemplate {
  id: string;
  title: string;
  prompt_text: string;
  category: string;
  created_at: string;
}

export interface TicketInsightSummary {
  ticket_id: string;
  ticket_subject: string;
  summary: string | null;
  sentiment: string | null;
  predicted_priority: string | null;
  suggested_tags: string[];
  generated_at: string;
}

export function askKnowledgeBase(question: string, topK = 4): Promise<RAGQueryResponse> {
  return request<RAGQueryResponse>("/ai-workspace/ask", {
    method: "POST",
    body: JSON.stringify({ question, top_k: topK }),
  });
}

export function listPrompts(): Promise<PromptTemplate[]> {
  return request<PromptTemplate[]>("/ai-workspace/prompts");
}

export function createPrompt(title: string, prompt_text: string, category = "general"): Promise<PromptTemplate> {
  return request<PromptTemplate>("/ai-workspace/prompts", {
    method: "POST",
    body: JSON.stringify({ title, prompt_text, category }),
  });
}

export function deletePrompt(id: string): Promise<void> {
  return request<void>(`/ai-workspace/prompts/${id}`, { method: "DELETE" });
}

export function listRecentInsights(limit = 20): Promise<TicketInsightSummary[]> {
  return request<TicketInsightSummary[]>(`/ai-workspace/insights?limit=${limit}`);
}