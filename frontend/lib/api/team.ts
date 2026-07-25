import { apiFetch } from "@/lib/api/client"; // adjust to match your existing fetch wrapper
import type {
  OrgMember, Team, TeamDetail, TeamCreateInput,
  Invitation, InvitationCreateInput, InvitationPreview, InvitationAcceptInput, UserRole,
} from "@/types/team";

export async function listMembers(): Promise<OrgMember[]> {
  return apiFetch<OrgMember[]>("/organizations/members");
}

export async function updateMemberRole(userId: string, role: UserRole): Promise<OrgMember> {
  return apiFetch<OrgMember>(`/organizations/members/${userId}`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

export async function listTeams(): Promise<Team[]> {
  return apiFetch<Team[]>("/teams/");
}

export async function createTeam(payload: TeamCreateInput): Promise<Team> {
  return apiFetch<Team>("/teams/", { method: "POST", body: JSON.stringify(payload) });
}

export async function getTeam(id: string): Promise<TeamDetail> {
  return apiFetch<TeamDetail>(`/teams/${id}`);
}

export async function addTeamMember(teamId: string, userId: string): Promise<void> {
  await apiFetch<void>(`/teams/${teamId}/members`, { method: "POST", body: JSON.stringify({ user_id: userId }) });
}

export async function removeTeamMember(teamId: string, userId: string): Promise<void> {
  await apiFetch<void>(`/teams/${teamId}/members/${userId}`, { method: "DELETE" });
}

export async function createInvitation(payload: InvitationCreateInput): Promise<Invitation> {
  return apiFetch<Invitation>("/invitations/", { method: "POST", body: JSON.stringify(payload) });
}

export async function listInvitations(): Promise<Invitation[]> {
  return apiFetch<Invitation[]>("/invitations/");
}

export async function revokeInvitation(id: string): Promise<void> {
  await apiFetch<void>(`/invitations/${id}`, { method: "DELETE" });
}

export async function previewInvitation(token: string): Promise<InvitationPreview> {
  return apiFetch<InvitationPreview>(`/invitations/token/${token}`);
}

export async function acceptInvitation(token: string, payload: InvitationAcceptInput): Promise<void> {
  await apiFetch<void>(`/invitations/token/${token}/accept`, { method: "POST", body: JSON.stringify(payload) });
}