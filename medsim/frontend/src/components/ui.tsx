/**
 * Shared presentational primitives: sections, stat tiles, chips, skeletons,
 * empty and error states, and the error boundary.
 *
 * The error surfaces get the most attention here because this application is a
 * QA target. `ErrorState` renders a *different* message per failure class and
 * always surfaces the request id, so a tester filing a bug has the one piece of
 * information that makes a server log searchable.
 */

import { Component, type ErrorInfo, type ReactNode } from 'react';

import { ApiParseError, ApiStatusError, errorMessageKey, errorRequestId } from '../api/client';
import { useI18n } from '../hooks/useApp';

// ---------------------------------------------------------------------------
// Layout
// ---------------------------------------------------------------------------

export function Section({
  id,
  title,
  count,
  children,
  actions,
  className = '',
}: {
  id?: string;
  title: string;
  count?: number;
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <section id={id} className={`scroll-mt-20 ${className}`} aria-labelledby={id ? `${id}-heading` : undefined}>
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <h2 id={id ? `${id}-heading` : undefined} className="text-xl">
          {title}
          {count !== undefined && (
            <span className="ml-2 text-base font-normal text-ink-muted tabular">{count}</span>
          )}
        </h2>
        {actions}
      </div>
      {children}
    </section>
  );
}

/**
 * A labelled value. Used throughout the case detail view for the dozens of
 * short field/value pairs, where a table would be heavier than the data.
 */
export function Field({
  label,
  children,
  className = '',
}: {
  label: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={className}>
      <dt className="overline">{label}</dt>
      <dd className="mt-0.5 break-clinical text-ink">{children}</dd>
    </div>
  );
}

export function StatTile({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <div className="card-padded" data-testid="stat-tile">
      <div className="overline">{label}</div>
      {/* A hero number with no plot needs no chart chrome - the number IS the
          visualisation. Proportional figures, per the type rules. */}
      <div className="mt-1 text-2xl font-semibold">{value}</div>
      {hint && <div className="mt-0.5 text-sm text-ink-secondary">{hint}</div>}
    </div>
  );
}

export function Chip({
  children,
  tone = 'neutral',
  onClick,
  active = false,
  testId,
}: {
  children: ReactNode;
  tone?: 'neutral' | 'accent';
  onClick?: () => void;
  active?: boolean;
  testId?: string;
}) {
  const base =
    'inline-flex items-center gap-1 rounded-pill px-2 py-0.5 text-label font-medium transition-colors';
  const tones = {
    neutral: 'bg-surface-sunken text-ink-secondary',
    accent: 'bg-accent-wash text-accent',
  };

  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        aria-pressed={active}
        data-testid={testId}
        className={`${base} ${active ? tones.accent : tones.neutral} hover:bg-accent-wash hover:text-accent`}
      >
        {children}
      </button>
    );
  }

  return (
    <span className={`${base} ${tones[tone]}`} data-testid={testId}>
      {children}
    </span>
  );
}

/** A 1-5 difficulty meter. Filled pips plus a text label - never colour alone. */
export function DifficultyMeter({ level }: { level: number }) {
  const { t } = useI18n();
  return (
    <span className="inline-flex items-center gap-1.5" title={t('difficulty.level', { level })}>
      <span className="flex gap-0.5" aria-hidden="true">
        {[1, 2, 3, 4, 5].map((pip) => (
          <span
            key={pip}
            className={`h-1.5 w-1.5 rounded-full ${pip <= level ? 'bg-accent' : 'bg-hairline'}`}
          />
        ))}
      </span>
      <span className="text-label text-ink-secondary">{t(`difficulty.${level}` as never)}</span>
      <span className="sr-only">{t('difficulty.level', { level })}</span>
    </span>
  );
}

// ---------------------------------------------------------------------------
// Loading & empty
// ---------------------------------------------------------------------------

export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`skeleton ${className}`} aria-hidden="true" />;
}

export function CaseCardSkeleton() {
  return (
    <div className="card-padded space-y-3" data-testid="case-skeleton">
      <Skeleton className="h-3 w-20" />
      <Skeleton className="h-5 w-full" />
      <Skeleton className="h-5 w-3/4" />
      <Skeleton className="h-12 w-full" />
      <div className="flex gap-2">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-16" />
      </div>
    </div>
  );
}

export function EmptyState({
  title,
  hint,
  action,
}: {
  title: string;
  hint?: string;
  action?: ReactNode;
}) {
  return (
    <div className="card-padded flex flex-col items-center py-12 text-center" data-testid="empty-state">
      <p className="text-lg font-medium">{title}</p>
      {hint && <p className="mt-1 max-w-prose text-sm text-ink-secondary">{hint}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const { t } = useI18n();
  const messageKey = errorMessageKey(error);
  const requestId = errorRequestId(error);
  const status = error instanceof ApiStatusError ? error.status : null;
  const isParse = error instanceof ApiParseError;

  return (
    <div
      className="card-padded border-critical/30 bg-critical-wash"
      role="alert"
      data-testid="error-state"
      data-error-kind={
        isParse ? 'parse' : status ? `status-${status}` : messageKey.replace('errors.', '')
      }
    >
      <h2 className="text-lg font-semibold">{t('errors.title')}</h2>
      <p className="mt-1 text-ink">{t(messageKey as never)}</p>

      {/* A malformed-JSON failure is almost always an intermediary rewriting
          the response, and saying so turns a mystifying error into an
          actionable one. */}
      {isParse && <p className="mt-2 max-w-prose text-sm text-ink-secondary">{t('errors.parseHint')}</p>}

      {status === 404 && <p className="mt-2 text-sm text-ink-secondary">{t('errors.notFoundHint')}</p>}

      <div className="mt-3 flex flex-wrap items-center gap-3">
        {onRetry && (
          <button type="button" className="btn-primary" onClick={onRetry} data-testid="error-retry">
            {t('actions.retry')}
          </button>
        )}
        <span className="text-label text-ink-muted tabular">
          {status !== null && <>{t('errors.statusCode', { code: status })} · </>}
          {requestId && t('errors.requestId', { id: requestId })}
        </span>
      </div>

      {isParse && (
        <details className="mt-3">
          <summary className="cursor-pointer text-sm text-ink-secondary">{t('errors.detail')}</summary>
          <pre className="scroll-x mt-2 max-h-40 rounded bg-surface-sunken p-2 text-label">
            {(error as ApiParseError).rawBody}
          </pre>
        </details>
      )}
    </div>
  );
}

interface BoundaryProps {
  children: ReactNode;
  /** Rendered instead of the default card, when a section needs a custom fallback. */
  fallback?: ReactNode;
}

interface BoundaryState {
  error: Error | null;
}

/**
 * Error boundary.
 *
 * Wrapped around each *section* of the case view rather than the whole page, so
 * that a malformed protocol payload blanks the protocol card and leaves the
 * labs, the chart and the diagnosis readable. On a clinical review screen,
 * partial information beats a blank page.
 */
export class SectionErrorBoundary extends Component<BoundaryProps, BoundaryState> {
  state: BoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): BoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('[boundary] section failed to render', error, info.componentStack);
  }

  render(): ReactNode {
    if (this.state.error) {
      return this.props.fallback ?? <BoundaryFallback error={this.state.error} />;
    }
    return this.props.children;
  }
}

function BoundaryFallback({ error }: { error: Error }) {
  const { t } = useI18n();
  return (
    <div className="card-padded" role="alert" data-testid="boundary-fallback">
      <p className="text-ink">{t('errors.boundary')}</p>
      <details className="mt-2">
        <summary className="cursor-pointer text-sm text-ink-secondary">{t('errors.detail')}</summary>
        <pre className="scroll-x mt-2 rounded bg-surface-sunken p-2 text-label">{error.message}</pre>
      </details>
    </div>
  );
}

/** A polite live region so filter changes are announced without stealing focus. */
export function LiveRegion({ message }: { message: string }) {
  return (
    <div aria-live="polite" aria-atomic="true" className="sr-only" data-testid="live-region">
      {message}
    </div>
  );
}
