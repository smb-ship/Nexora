// components/layout/MobileSidebar.tsx
"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { navigation, bottomNavigation } from "@/lib/navigation";

export function MobileSidebar() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  const allItems = [...navigation, ...bottomNavigation];

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
  render={
    <Button
      variant="ghost"
      size="icon"
      className="md:hidden text-foreground-muted"
    >
      <Menu className="h-5 w-5" />
    </Button>
  }
/>
      <SheetContent side="left" className="w-64 bg-surface border-border p-0">
        <div className="flex h-16 items-center gap-2 px-6 border-b border-border-subtle">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
            <Sparkles className="h-4 w-4 text-primary-foreground" />
          </div>
          <span className="text-[15px] font-semibold text-foreground tracking-tight">
            Nexora
          </span>
        </div>
        <nav className="flex flex-1 flex-col px-3 py-4">
  <ul className="space-y-0.5">
    {navigation.map((item) => {
      const isActive = pathname.startsWith(item.href);
      const Icon = item.icon;
      return (
        <li key={item.href}>
          <Link
            href={item.href}
            onClick={() => setOpen(false)}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
              isActive
                ? "bg-primary/10 text-primary font-medium"
                : "text-foreground-muted hover:bg-surface-elevated hover:text-foreground"
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            {item.label}
          </Link>
        </li>
      );
    })}
  </ul>

  <div className="mt-auto border-t border-border pt-4">
    <ul className="space-y-0.5">
      {bottomNavigation.map((item) => {
        const isActive = pathname.startsWith(item.href);
        const Icon = item.icon;
        return (
          <li key={item.href}>
            <Link
              href={item.href}
              onClick={() => setOpen(false)}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-foreground-muted hover:bg-surface-elevated hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {item.label}
            </Link>
          </li>
        );
      })}
    </ul>
  </div>
</nav>
      </SheetContent>
    </Sheet>
  );
}