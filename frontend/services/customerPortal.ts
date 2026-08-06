import type {
  CustomerTicketListResponse, CustomerTicketDetail, CustomerTicketCreateInput,
  CustomerComment, CustomerDashboardStats, CustomerTicketStatus, CustomerTicketCategory,
} from "@/types/customerPortal";

const API_BASE_URL = `${process.env.NEXT_PUBLIC_API_URL ?? ""}/api/v1`;

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with status ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const customerPortalService = {
  dashboard: () => request<CustomerDashboardStats>("/portal/dashboard"),

  listTickets: (params: {
    q?: string;
    status?: CustomerTicketStatus;
    category?: CustomerTicketCategory;
    skip?: number;
    limit?: number;
  } = {}) => {
    const query = new URLSearchParams();
    if (params.q) query.set("q", params.q);
    if (params.status) query.set("status", params.status);
    if (params.category) query.set("category", params.category);
    query.set("skip", String(params.skip ?? 0));
    query.set("limit", String(params.limit ?? 20));
    return request<CustomerTicketListResponse>(`/portal/tickets?${query.toString()}`);
  },

  getTicket: (id: string) => request<CustomerTicketDetail>(`/portal/tickets/${id}`),

  createTicket: (payload: CustomerTicketCreateInput) =>
    request<CustomerTicketDetail>("/portal/tickets", { method: "POST", body: JSON.stringify(payload) }),

  listComments: (ticketId: string) => request<CustomerComment[]>(`/portal/tickets/${ticketId}/comments`),

  addComment: (ticketId: string, body: string) =>
    request<CustomerComment>(`/portal/tickets/${ticketId}/comments`, {
      method: "POST",
      body: JSON.stringify({ body }),
    }),
};