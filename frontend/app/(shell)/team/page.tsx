"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { UserPlus } from "lucide-react";
import { MembersTable } from "@/components/team/MembersTable";
import { PendingInvitesList } from "@/components/team/PendingInvitesList";
import { TeamsPanel } from "@/components/team/TeamsPanel";
import { InviteSheet } from "@/components/team/InviteSheet";
import { usePermission } from "@/hooks/use-permission";
import { listMembers, listInvitations } from "@/lib/api/team";
import type { OrgMember, Invitation } from "@/types/team";

type Tab = "members" | "teams";

export default function TeamPage() {
  const [tab, setTab] = useState<Tab>("members");
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [inviteOpen, setInviteOpen] = useState(false);
  const canInvite = usePermission("team:invite");

  useEffect(() => {
    listMembers().then(setMembers);
    if (canInvite) listInvitations().then(setInvitations);
  }, [canInvite]);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Team</h1>
          <div className="mt-3 flex gap-1">
            <button
              onClick={() => setTab("members")}
              className={`rounded-md px-3 py-1.5 text-sm ${tab === "members" ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-muted"}`}
            >
              Members
            </button>
            <button
              onClick={() => setTab("teams")}
              className={`rounded-md px-3 py-1.5 text-sm ${tab === "teams" ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-muted"}`}
            >
              Teams
            </button>
          </div>
        </div>
        {canInvite && (
          <Button onClick={() => setInviteOpen(true)}>
            <UserPlus className="mr-1.5 size-4" />
            Invite member
          </Button>
        )}
      </div>

      {tab === "members" ? (
        <div className="space-y-6">
          <MembersTable members={members} onMemberUpdated={(u) => setMembers((prev) => prev.map((m) => (m.id === u.id ? u : m)))} />
          {canInvite && (
            <div>
              <h2 className="mb-2 text-sm font-medium text-muted-foreground">Pending invitations</h2>
              <PendingInvitesList invitations={invitations} onRevoked={(id) => setInvitations((prev) => prev.filter((i) => i.id !== id))} />
            </div>
          )}
        </div>
      ) : (
        <TeamsPanel />
      )}

      <InviteSheet open={inviteOpen} onOpenChange={setInviteOpen} onInvited={(inv) => setInvitations((prev) => [inv, ...prev])} />
    </div>
  );
}