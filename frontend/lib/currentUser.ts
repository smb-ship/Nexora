// Minimal current-user fetcher used to gate portal vs. agent shell access.
// I don't have your existing auth hook/context, so this calls /auth/me
// directly (confirmed to exist from your dev server logs). If you already
// have a useAuth/useCurrentUser hook, tell me and I'll swap this out for it.

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string | null;
  role: "owner" | "admin" | "manager" | "agent" | "viewer" | "customer";
  organization_id: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function fetchCurrentUser(): Promise<CurrentUser | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/me`, { credentials: "include" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}