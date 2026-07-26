import {
  LayoutDashboard,
  Inbox,
  Ticket,
  Users,
  BookOpen,
  Sparkles,
  BarChart3,
  Workflow,
  UsersRound,
  Settings,
  MessageCircle,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export const navigation: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Inbox", href: "/inbox", icon: Inbox },
  { label: "Live Chat", href: "/chat", icon: MessageCircle },
  { label: "Tickets", href: "/tickets", icon: Ticket },
  { label: "Customers", href: "/crm", icon: Users },
  { label: "Knowledge Hub", href: "/knowledge", icon: BookOpen },
  { label: "AI Workspace", href: "/ai-workspace", icon: Sparkles },
  { label: "Business Intelligence", href: "/analytics", icon: BarChart3 },
  { label: "Automation", href: "/workflows", icon: Workflow },
  { label: "Integrations", href: "/automation", icon: Workflow },
  { label: "Team", href: "/team", icon: UsersRound },
];

export const bottomNavigation: NavItem[] = [
  { label: "Settings", href: "/settings", icon: Settings },
];