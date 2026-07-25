"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus } from "lucide-react";
import { usePermission } from "@/hooks/use-permission";
import { listTeams, createTeam } from "@/lib/api/team";
import type { Team } from "@/types/team";

export function TeamsPanel() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [newTeamName, setNewTeamName] = useState("");
  const [creating, setCreating] = useState(false);
  const canManageTeams = usePermission("team:manage");

  useEffect(() => {
    listTeams().then(setTeams);
  }, []);

  async function handleCreate() {
    if (!newTeamName.trim()) return;
    setCreating(true);
    try {
      setTeams((prev) => [...prev, ...[]]); // no-op placeholder removed below
      const team = await createTeam({ name: newTeamName });
      setTeams((prev) => [...prev, team]);
      setNewTeamName("");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-4">
      {canManageTeams && (
        <div className="flex gap-2">
          <Input value={newTeamName} onChange={(e) => setNewTeamName(e.target.value)} placeholder="New team name" className="max-w-xs" />
          <Button onClick={handleCreate} disabled={creating || !newTeamName.trim()}>
            <Plus className="mr-1.5 size-4" />
            Create team
          </Button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {teams.map((team) => (
          <div key={team.id} className="rounded-lg border border-border p-4">
            <p className="font-medium">{team.name}</p>
            <p className="text-sm text-muted-foreground">{team.member_count} member{team.member_count === 1 ? "" : "s"}</p>
          </div>
        ))}
        {teams.length === 0 && <p className="text-sm text-muted-foreground">No teams yet.</p>}
      </div>
    </div>
  );
}