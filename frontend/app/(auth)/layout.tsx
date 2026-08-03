import Link from "next/link";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-4">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(circle at 50% 0%, color-mix(in srgb, var(--color-primary) 12%, transparent), transparent 60%)",
        }}
      />

      <div className="relative w-full max-w-sm">
        <Link href="/" className="mb-8 flex items-center justify-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
            N
          </span>
          <span className="text-lg font-semibold tracking-tight text-foreground">Nexora</span>
        </Link>

        <div className="animate-in fade-in slide-in-from-bottom-2 duration-500 rounded-xl border border-border bg-surface-elevated p-8 shadow-lg">
          {children}
        </div>
      </div>
    </div>
  );
}