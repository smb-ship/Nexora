"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { fetchCurrentUser } from "@/lib/currentUser";

export default function ShellLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    let active = true;
    fetchCurrentUser().then((user) => {
      if (!active) return;
      if (user?.role === "customer") {
        router.replace("/portal/dashboard");
        return;
      }
      setChecked(true);
    });
    return () => {
      active = false;
    };
  }, [router]);

  if (!checked) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-3 bg-background">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
        <p className="text-sm text-foreground-muted">Loading Nexora...</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <div className="flex flex-1 flex-col min-w-0">
        <Topbar />

        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="animate-in fade-in duration-300">{children}</div>
        </main>
      </div>
    </div>
  );
}