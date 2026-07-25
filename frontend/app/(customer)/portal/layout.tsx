"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchCurrentUser } from "@/lib/currentUser";
import { PortalNav } from "@/components/customer-portal/PortalNav";

export default function PortalLayout({
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
      if (!user) {
        router.replace("/login");
        return;
      }
      if (user.role !== "customer") {
        router.replace("/dashboard");
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
      <div className="flex h-screen items-center justify-center bg-background text-sm text-foreground-muted">
        Loading...
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <PortalNav />
      <main className="flex-1 overflow-y-auto p-4 md:p-6">{children}</main>
    </div>
  );
}