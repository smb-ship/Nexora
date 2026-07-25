"use client";

import { Button } from "@/components/ui/button";
import { RoleBadge } from "./RoleBadge";
import { revokeInvitation } from "@/lib/api/team";
import type { Invitation } from "@/types/team";

interface PendingInvitesListProps {
  invitations: Invitation[];
  onRevoked: (id: string) => void;
}

export function PendingInvitesList({ invitations, onRevoked }: PendingInvitesListProps) {
  async function handleRevoke(id: string) {
    await revokeInvitation(id);
    onRevoked(id);
  }

  if (invitations.length === 0) {
    return <p className="text-sm text-muted-foreground">No pending invitations.</p>;
  }

  return (
    <div className="space-y-2">
      {invitations.map((invitation) => (
        <div key={invitation.id} className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
          <div className="flex items-center gap-2">
            <span className="text-sm">{invitation.email}</span>
            <RoleBadge role={invitation.role} />
          </div>
          <Button size="sm" variant="ghost" onClick={() => handleRevoke(invitation.id)}>Revoke</Button>
        </div>
      ))}
    </div>
  );
}