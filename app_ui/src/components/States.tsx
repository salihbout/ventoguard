import { Alert, Button, Spinner } from "@databricks/design-system";

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="state" role="status" aria-live="polite">
      <Spinner size="default" />
      <span className="small">{label}…</span>
    </div>
  );
}

export function SkeletonBlock({ height = 120 }: { height?: number }) {
  return <div className="skeleton" style={{ height }} aria-hidden="true" />;
}

export function Empty({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="state">
      <strong style={{ color: "var(--db-text-primary)" }}>{title}</strong>
      {children && <span className="small">{children}</span>}
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : String(error);
  return (
    <Alert
      componentId="vg.error"
      type="error"
      closable={false}
      message="Could not load this data"
      description={
        <span>
          {message}{" "}
          {onRetry && (
            <Button componentId="vg.error.retry" size="small" onClick={onRetry}>
              Retry
            </Button>
          )}
        </span>
      }
    />
  );
}
