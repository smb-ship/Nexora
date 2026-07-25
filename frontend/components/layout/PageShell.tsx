// components/layout/PageShell.tsx
export function PageShell({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <h1 className="text-xl font-semibold text-foreground tracking-tight">
        {title}
      </h1>
      {description && (
        <p className="text-sm text-foreground-muted">{description}</p>
      )}
      <div className="mt-6 flex h-64 items-center justify-center rounded-lg border border-dashed border-border text-sm text-foreground-subtle">
        This section is built in a later milestone.
      </div>
    </div>
  );
}