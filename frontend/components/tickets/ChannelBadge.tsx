import { Globe, Users, Mail } from "lucide-react";
import type { TicketSource } from "@/types/ticket";

const CONFIG: Record<TicketSource, { icon: typeof Globe; label: string }> = {
  web: { icon: Globe, label: "Web" },
  customer_portal: { icon: Users, label: "Portal" },
  email: { icon: Mail, label: "Email" },
};

export function ChannelBadge({ source }: { source: TicketSource }) {
  const { icon: Icon, label } = CONFIG[source];
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
      <Icon className="h-3 w-3" />
      {label}
    </span>
  );
}