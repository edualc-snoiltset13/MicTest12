/**
 * Result flag badge and sparkline.
 *
 * The badge is the component where the accessibility rule bites hardest: a lab
 * flag is a clinical judgement, and it must never be carried by colour alone.
 * Each badge therefore renders THREE redundant channels:
 *
 *   1. a background wash (colour)
 *   2. a directional glyph (shape) - up/down arrows, doubled when critical
 *   3. the HL7 short code as text, plus a translated full name in the
 *      accessible name and tooltip
 *
 * A greyscale printout, a deuteranopic reader and a screen-reader user all get
 * the same information.
 */

import type { ResultFlag } from '../api/types';
import { useI18n } from '../hooks/useApp';

/** Directional glyphs. Chosen for shape distinctness, not decoration. */
const GLYPH: Record<ResultFlag, string> = {
  N: '',
  H: '▲',
  L: '▼',
  HH: '▲▲',
  LL: '▼▼',
  A: '!',
};

export function FlagBadge({ flag, showLabel = false }: { flag: ResultFlag; showLabel?: boolean }) {
  const { t } = useI18n();
  const fullName = t(`flag.${flag}` as never);
  const shortCode = t(`flag.short.${flag}` as never);

  // A normal result gets no badge in dense tables: flagging everything flags
  // nothing, and the absence of a badge is itself the signal.
  if (flag === 'N' && !showLabel) {
    return (
      <span className="sr-only" data-testid="flag-N">
        {fullName}
      </span>
    );
  }

  return (
    <span
      className={`flag-badge flag-${flag}`}
      title={fullName}
      data-testid={`flag-${flag}`}
      data-flag={flag}
    >
      {GLYPH[flag] && <span aria-hidden="true">{GLYPH[flag]}</span>}
      <span aria-hidden="true">{shortCode}</span>
      <span className="sr-only">{fullName}</span>
      {showLabel && (
        <span className="ml-0.5 font-normal not-sr-only" aria-hidden="true">
          {fullName}
        </span>
      )}
    </span>
  );
}

/**
 * A 1-line-tall trend indicator for the case grid.
 *
 * Deliberately unlabelled and non-interactive: it answers "is this going up or
 * down?" at a glance and defers everything else to the full chart. It carries
 * `aria-hidden` because the adjacent text already states the trend - a screen
 * reader announcing a shape is noise.
 */
export function Sparkline({
  values,
  width = 64,
  height = 20,
  className = '',
}: {
  values: number[];
  width?: number;
  height?: number;
  className?: string;
}) {
  if (values.length < 2) return null;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const step = width / (values.length - 1);

  const path = values
    .map((value, index) => {
      const x = index * step;
      // 2px inset top and bottom so the stroke is never clipped by the box.
      const y = height - 2 - ((value - min) / span) * (height - 4);
      return `${index === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');

  const rising = values[values.length - 1]! > values[0]!;

  return (
    <svg
      className={`sparkline ${className}`}
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      aria-hidden="true"
      focusable="false"
    >
      <path
        d={path}
        fill="none"
        stroke={`rgb(var(${rising ? '--c-series-2' : '--c-series-1'}))`}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle
        cx={width}
        cy={height - 2 - ((values[values.length - 1]! - min) / span) * (height - 4)}
        r={2}
        fill={`rgb(var(${rising ? '--c-series-2' : '--c-series-1'}))`}
      />
    </svg>
  );
}
