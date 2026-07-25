import type { UserRole } from "@/types/team";

export type Permission =
  | "ticket:create"
  | "ticket:update_status"
  | "ticket:update_priority"
  | "ticket:assign"
  | "ticket:delete"
  | "ticket:comment"
  | "ticket:internal_note"
  | "team:manage"
  | "team:invite"
  | "team:role_manage"
  | "team:member_remove";

const ALL_TICKET: Permission[] = [
  "ticket:create", "ticket:update_status", "ticket:update_priority",
  "ticket:assign", "ticket:delete", "ticket:comment", "ticket:internal_note",
];
const ALL_TEAM: Permission[] = ["team:manage", "team:invite", "team:role_manage", "team:member_remove"];

const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  owner: [...ALL_TICKET, ...ALL_TEAM],
  admin: [...ALL_TICKET, ...ALL_TEAM],
  manager: ["ticket:create", "ticket:update_status", "ticket:update_priority", "ticket:assign", "ticket:comment", "ticket:internal_note", "team:manage", "team:invite"],
  agent: ["ticket:create", "ticket:update_status", "ticket:update_priority", "ticket:assign", "ticket:comment", "ticket:internal_note"],
  viewer: [],
};

export function hasPermission(role: UserRole | undefined, permission: Permission): boolean {
  if (!role) return false;
  return ROLE_PERMISSIONS[role].includes(permission);
}