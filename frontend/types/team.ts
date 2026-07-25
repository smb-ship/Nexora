export type UserRole = "owner" | "admin" | "manager" | "agent" | "viewer";

export interface OrgMember {
  id: string;
  full_name: string | null;
  email: string;
  role: UserRole;
  created_at: string;
}

export interface Team {
  id: string;
  name: string;
  created_at: string;
  member_count: number;
}

export interface TeamMember {
  id: string;
  full_name: string | null;
  email: string;
}

export interface TeamDetail extends Team {
  members: TeamMember[];
}

export interface TeamCreateInput {
  name: string;
}

export interface Invitation {
  id: string;
  email: string;
  role: UserRole;
  token: string;
  status: string;
  created_at: string;
  expires_at: string;
}

export interface InvitationCreateInput {
  email: string;
  role: UserRole;
}

export interface InvitationPreview {
  email: string;
  role: UserRole;
  organization_name: string;
  valid: boolean;
}

export interface InvitationAcceptInput {
  full_name: string;
  password: string;
}