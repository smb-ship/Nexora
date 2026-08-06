const API_BASE = `${process.env.NEXT_PUBLIC_API_URL ?? ""}/api/v1`;

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

export interface KnowledgeArticleListItem {
  id: string;
  title: string;
  tags: string[];
  status: "draft" | "published";
  view_count: number;
  updated_at: string;
}

export interface KnowledgeArticle extends KnowledgeArticleListItem {
  body: string;
  author_id: string;
  created_at: string;
  published_at: string | null;
}

export interface SuggestedArticle {
  id: string;
  title: string;
  tags: string[];
  reason: string;
}

export function listArticles(params?: { search?: string; status?: string; tag?: string }): Promise<KnowledgeArticleListItem[]> {
  const query = new URLSearchParams();
  if (params?.search) query.set("search", params.search);
  if (params?.status) query.set("status", params.status);
  if (params?.tag) query.set("tag", params.tag);
  const qs = query.toString();
  return request<KnowledgeArticleListItem[]>(`/knowledge/articles${qs ? `?${qs}` : ""}`);
}

export function getArticle(id: string): Promise<KnowledgeArticle> {
  return request<KnowledgeArticle>(`/knowledge/articles/${id}`);
}

export function createArticle(payload: { title: string; body: string; tags: string[]; status: string }): Promise<KnowledgeArticle> {
  return request<KnowledgeArticle>("/knowledge/articles", { method: "POST", body: JSON.stringify(payload) });
}

export function updateArticle(id: string, payload: Partial<{ title: string; body: string; tags: string[]; status: string }>): Promise<KnowledgeArticle> {
  return request<KnowledgeArticle>(`/knowledge/articles/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function deleteArticle(id: string): Promise<void> {
  return request<void>(`/knowledge/articles/${id}`, { method: "DELETE" });
}

export function suggestArticlesForTicket(ticketId: string): Promise<SuggestedArticle[]> {
  return request<SuggestedArticle[]>(`/knowledge/articles/suggest?ticket_id=${ticketId}`);
}