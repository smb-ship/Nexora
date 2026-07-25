"use client";
import { useRouter } from "next/navigation";
import { Bell, Search, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Avatar,
  AvatarFallback,
} from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MobileSidebar } from "./MobileSidebar";
import { useAuth } from "@/lib/auth-context";

function getInitials(name: string | null, email: string) {
  if (name && name.trim().length > 0) {
    const parts = name.trim().split(/\s+/);
    const first = parts[0]?.[0] ?? "";
    const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
    return (first + last).toUpperCase();
  }
  return email.slice(0, 2).toUpperCase();
}

export function Topbar() {
  const router = useRouter();
  const { user, logout } = useAuth();

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  const initials = user ? getInitials(user.full_name, user.email) : "";

  return (
    <header className="sticky top-0 z-10 flex h-16 items-center gap-4 border-b border-border-subtle bg-background/80 backdrop-blur px-4 md:px-6">
      {/* Mobile menu trigger */}
      <MobileSidebar />
      {/* Search */}
      <div className="flex flex-1 items-center gap-2 rounded-md border border-border bg-surface px-3 py-2 max-w-md">
        <Search className="h-4 w-4 text-foreground-subtle" />
        <input
          type="text"
          placeholder="Search tickets, customers, articles…"
          className="w-full bg-transparent text-sm text-foreground placeholder:text-foreground-subtle outline-none"
        />
      </div>
      <div className="flex-1" />
      {/* Notifications */}
      <Button variant="ghost" size="icon" className="text-foreground-muted">
        <Bell className="h-4 w-4" />
      </Button>
      {/* User menu */}
      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <button className="flex items-center gap-2 rounded-full outline-none focus-visible:ring-2 focus-visible:ring-primary">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-primary/10 text-primary text-xs font-medium">
                  {initials}
                </AvatarFallback>
              </Avatar>
            </button>
          }
        />
        <DropdownMenuContent align="end" className="w-48">
          <DropdownMenuItem>Profile</DropdownMenuItem>
          <DropdownMenuItem>Settings</DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem className="text-destructive" onClick={handleLogout}>
            Log out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}