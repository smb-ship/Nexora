// Minimal current-user fetcher used to gate portal vs. agent shell access.

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string | null;
  role: "owner" | "admin" | "manager" | "agent" | "viewer" | "customer";
  organization_id: string;
}

const API_BASE_URL = `${process.env.NEXT_PUBLIC_API_URL ?? ""}/api/v1`;

export async function fetchCurrentUser(): Promise<CurrentUser | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/me`, { credentials: "include" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}