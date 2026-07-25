"use client";

import { RoleBadge } from "./RoleBadge";
import { RoleSelect } from "./RoleSelect";
import { usePermission } from "@/hooks/use-permission";
import { updateMemberRole } from "@/lib/api/team";
import type { OrgMember, UserRole } from "@/types/team";

interface MembersTableProps {
  members: OrgMember[];
  onMemberUpdated: (member: OrgMember) => void;
}

export function MembersTable({ members, onMemberUpdated }: MembersTableProps) {
  const canManageRoles = usePermission("team:role_manage");

  async function handleRoleChange(member: OrgMember, role: UserRole) {
    onMemberUpdated(await updateMemberRole(member.id, role));
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-left text-muted-foreground">
          <tr>
            <th className="px-4 py-3 font-medium">Name</th>
            <th className="px-4 py-3 font-medium">Email</th>
            <th className="px-4 py-3 font-medium">Role</th>
          </tr>
        </thead>
        <tbody>
          {members.map((member) => (
            <tr key={member.id} className="border-t border-border">
              <td className="px-4 py-3 font-medium">{member.full_name || "—"}</td>
              <td className="px-4 py-3 text-muted-foreground">{member.email}</td>
              <td className="px-4 py-3">
                {canManageRoles && member.role !== "owner" ? (
                  <RoleSelect value={member.role} onChange={(role) => handleRoleChange(member, role)} />
                ) : (
                  <RoleBadge role={member.role} />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}