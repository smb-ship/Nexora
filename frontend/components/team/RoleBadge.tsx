import { Badge } from "@/components/ui/badge";
import type { UserRole } from "@/types/team";

const ROLE_STYLES: Record<UserRole, string> = {
  owner: "bg-purple-500/15 text-purple-400 border-purple-500/30",
  admin: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  manager: "bg-teal-500/15 text-teal-400 border-teal-500/30",
  agent: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
  viewer: "bg-zinc-500/10 text-zinc-500 border-zinc-500/20",
};

const ROLE_LABELS: Record<UserRole, string> = {
  owner: "Owner", admin: "Admin", manager: "Manager", agent: "Agent", viewer: "Viewer",
};

export function RoleBadge({ role }: { role: UserRole }) {
  return <Badge variant="outline" className={ROLE_STYLES[role]}>{ROLE_LABELS[role]}</Badge>;
}