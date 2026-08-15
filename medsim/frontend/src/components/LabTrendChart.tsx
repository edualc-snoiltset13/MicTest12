/**
 * Lab trend chart.
 *
 * Hand-rolled SVG rather than a charting library, for reasons that are specific
 * to this chart rather than general preference:
 *
 *  - The **shaded reference interval** is the whole point of a lab chart, and
 *    every general-purpose library makes it an awkward annotation layer.
 *  - **Per-point flag styling** (a critical value must be visually distinct
 *    from a merely high one) needs mark-level control.
 *  - The bundle is ~4 KB instead of ~90 KB, which matters on the mobile
 *    wrapper the Phase 3 suite drives over a throttled 3G connection.
 *
 * Design rules applied (see the ADR for the reasoning):
 *
 *  - **One y-axis, always.** Analytes with different units get their own chart
 *    (small multiples), never a second axis. A TSH of 68 and an FT4 of 6 share
 *    no scale, and drawing them against two axes invites a causal reading of
 *    what is really two independent series. This is why the compare mode
 *    normalises to percent-of-reference-range rather than plotting raw units.
 *  - 2px line, round caps; markers r=4 with a 2px surface ring so they stay
 *    legible where they cross the line.
 *  - Reference band as a 10% wash behind everything, never a saturated block.
 *  - A single series carries no legend - the heading names it. Two or three
 *    series get a legend AND direct endpoint labels, so identity never rests
 *    on colour alone.
 *  - Only the endpoint is labelled. A number on every point is unreadable.
 *  - Every chart ships an equivalent data table, reachable by a toggle and
 *    always present for screen readers.
 */

import { useCallback, useId, useMemo, useState } from 'react';

import { useElementWidth } from '../hooks/useAsync';
import { useI18n } from '../hooks/useApp';
import type { AnalyteTrend, ResultFlag } from '../api/types';
import { FlagBadge } from './FlagBadge';

const MARGIN = { top: 16, right: 64, bottom: 40, left: 56 } as const;
const HEIGHT = 260;
const MIN_WIDTH = 280;

/** Categorical slots 1-3. Validated all-pairs for CVD in both themes. */
const SERIES_VARS = ['--c-series-1', '--c-series-2', '--c-series-3'] as const;

interface Props {
  series: AnalyteTrend[];
  /** Rendered as the chart's accessible name; a single series needs no legend. */
  title?: string;
  /** Percent-of-range normalisation, used when comparing different units. */
  normalise?: boolean;
  className?: string;
}

interface Scales {
  xScale: (day: number) => number;
  yScale: (value: number) => number;
  xTicks: number[];
  yTicks: number[];
  innerWidth: number;
  innerHeight: number;
  yMin: number;
  yMax: number;
}

/**
 * Produces 4-6 ticks at 1/2/5 x 10^n intervals. Clean tick values are what let
 * a reader estimate an unlabelled point; ticks at 3.7 / 7.4 / 11.1 do not.
 */
function niceTicks(min: number, max: number, target = 5): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max)) return [];
  if (min === max) return [min];
  const span = max - min;
  const rawStep = span / target;
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const normalised = rawStep / magnitude;
  const step = (normalised >= 5 ? 10 : normalised >= 2 ? 5 : normalised >= 1 ? 2 : 1) * magnitude;
  const start = Math.ceil(min / step) * step;
  const ticks: number[] = [];
  for (let value = start; value <= max + step * 1e-9; value += step) {
    // Guard against binary drift producing 0.30000000000000004 as a tick.
    ticks.push(Number(value.toFixed(10)));
  }
  return ticks;
}

/** Converts a raw value to percent-of-reference-range for the compare view. */
function normaliseValue(value: number, low: number | null, high: number | null): number {
  if (low === null || high === null || high === low) return value;
  return ((value - low) / (high - low)) * 100;
}

export function LabTrendChart({ series, title, normalise = false, className = '' }: Props) {
  const { t, fmt } = useI18n();
  const [containerRef, measuredWidth] = useElementWidth<HTMLDivElement>();
  const [view, setView] = useState<'chart' | 'table'>('chart');
  const [hoverDay, setHoverDay] = useState<number | null>(null);
  const chartId = useId();

  const width = Math.max(measuredWidth || MIN_WIDTH, MIN_WIDTH);
  const innerWidth = Math.max(width - MARGIN.left - MARGIN.right, 40);
  const innerHeight = HEIGHT - MARGIN.top - MARGIN.bottom;

  const visible = series.slice(0, SERIES_VARS.length);
  const primary = visible[0];
  const isMulti = visible.length > 1;

  const scales = useMemo<Scales | null>(() => {
    if (!primary || primary.points.length === 0) return null;

    const allDays = visible.flatMap((s) => s.points.map((p) => p.day_offset));
    const xMin = Math.min(...allDays);
    const xMaxRaw = Math.max(...allDays);
    // A single-point series would otherwise divide by zero.
    const xMax = xMaxRaw === xMin ? xMin + 1 : xMaxRaw;

    const values = visible.flatMap((s) =>
      s.points.map((p) => (normalise && isMulti ? normaliseValue(p.value, s.ref_low, s.ref_high) : p.value)),
    );

    // The reference band must be inside the domain even when every measured
    // value sits far outside it - otherwise the band silently disappears and
    // the reader loses the only context the chart provides.
    const bandValues: number[] = [];
    if (!isMulti || !normalise) {
      for (const s of visible) {
        if (s.ref_low !== null) bandValues.push(s.ref_low);
        if (s.ref_high !== null) bandValues.push(s.ref_high);
      }
    } else {
      bandValues.push(0, 100);
    }

    const domainValues = [...values, ...bandValues];
    const rawMin = Math.min(...domainValues);
    const rawMax = Math.max(...domainValues);
    const pad = (rawMax - rawMin) * 0.12 || Math.abs(rawMax) * 0.12 || 1;

    // Never extend a lab axis below zero: a negative concentration is not a
    // thing, and the empty band below zero reads as meaningful space.
    const yMin = Math.max(0, rawMin - pad);
    const yMax = rawMax + pad;

    const xScale = (day: number) => ((day - xMin) / (xMax - xMin)) * innerWidth;
    const yScale = (value: number) => innerHeight - ((value - yMin) / (yMax - yMin)) * innerHeight;

    // Ticks land on actual sampling days, so the axis never implies a
    // measurement that was not taken. Candidate ticks are then thinned so that
    // two labels can never overprint: sampling days are often clustered (day 0
    // and day 14, say), and at typical widths those labels collide into
    // unreadable strings like "014". Keeping the first and last and dropping
    // crowded intermediates is better than a legible-but-fictional even grid.
    const uniqueDays = Array.from(new Set(allDays)).sort((a, b) => a - b);
    const candidates = uniqueDays.length <= 8 ? uniqueDays : niceTicks(xMin, xMax, 5);
    const MIN_TICK_GAP_PX = 34;
    const xTicks: number[] = [];
    for (const day of candidates) {
      const previous = xTicks[xTicks.length - 1];
      if (previous === undefined || xScale(day) - xScale(previous) >= MIN_TICK_GAP_PX) {
        xTicks.push(day);
      }
    }
    // The final sample is the one a reader looks for; if thinning dropped it,
    // put it back and remove whichever neighbour it now crowds.
    const finalDay = uniqueDays[uniqueDays.length - 1];
    if (finalDay !== undefined && xTicks[xTicks.length - 1] !== finalDay) {
      while (
        xTicks.length > 0 &&
        xScale(finalDay) - xScale(xTicks[xTicks.length - 1]!) < MIN_TICK_GAP_PX
      ) {
        xTicks.pop();
      }
      xTicks.push(finalDay);
    }

    return {
      xScale,
      yScale,
      xTicks,
      yTicks: niceTicks(yMin, yMax, 5),
      innerWidth,
      innerHeight,
      yMin,
      yMax,
    };
  }, [visible, primary, innerWidth, innerHeight, normalise, isMulti]);

  const valueOf = useCallback(
    (s: AnalyteTrend, raw: number) => (normalise && isMulti ? normaliseValue(raw, s.ref_low, s.ref_high) : raw),
    [normalise, isMulti],
  );

  const handlePointer = useCallback(
    (event: React.PointerEvent<SVGRectElement>) => {
      if (!scales || !primary) return;
      const rect = event.currentTarget.getBoundingClientRect();
      const x = event.clientX - rect.left;
      // Snap to the nearest actual measurement rather than interpolating: a
      // crosshair between two samples would imply a value nobody measured.
      let nearest: number | null = null;
      let nearestDistance = Infinity;
      for (const point of primary.points) {
        const distance = Math.abs(scales.xScale(point.day_offset) - x);
        if (distance < nearestDistance) {
          nearestDistance = distance;
          nearest = point.day_offset;
        }
      }
      setHoverDay(nearest);
    },
    [scales, primary],
  );

  if (!primary || primary.points.length === 0 || !scales) {
    return (
      <div className={`card-padded ${className}`} data-testid="chart-empty">
        <p className="text-sm text-ink-secondary">{t('chart.noData')}</p>
      </div>
    );
  }

  const decimals = primary.decimals ?? 2;
  const firstPoint = primary.points[0]!;
  const lastPoint = primary.points[primary.points.length - 1]!;
  const singlePoint = primary.points.length === 1;

  const accessibleSummary = t('chart.accessibleSummary', {
    analyte: primary.analyte_name,
    count: primary.points.length,
    firstDay: firstPoint.day_offset,
    lastDay: lastPoint.day_offset,
    first: fmt.labValue(firstPoint.value, decimals),
    last: fmt.labValue(lastPoint.value, decimals),
    unit: primary.unit ?? '',
    low: primary.ref_low !== null ? fmt.labValue(primary.ref_low, decimals) : '-',
    high: primary.ref_high !== null ? fmt.labValue(primary.ref_high, decimals) : '-',
  });

  const hoveredPoints = hoverDay === null
    ? []
    : visible
        .map((s) => ({ series: s, point: s.points.find((p) => p.day_offset === hoverDay) }))
        .filter((entry): entry is { series: AnalyteTrend; point: NonNullable<typeof entry.point> } => !!entry.point);

  return (
    <figure className={`card min-w-0 ${className}`} data-testid="lab-trend-chart" data-analyte={primary.analyte_code}>
      {/* ---- header: title, latest value, view toggle -------------------- */}
      <figcaption className="flex flex-wrap items-start justify-between gap-3 border-b border-hairline p-4 pb-3">
        <div className="min-w-0">
          <h3 className="text-lg font-semibold break-clinical">
            {title ?? primary.analyte_name}
          </h3>
          <p className="mt-0.5 text-sm text-ink-secondary">
            {isMulti && normalise
              ? t('chart.subtitle')
              : t('chart.referenceBandDescription', {
                  low: primary.ref_low !== null ? fmt.labValue(primary.ref_low, decimals) : '-',
                  high: primary.ref_high !== null ? fmt.labValue(primary.ref_high, decimals) : '-',
                  unit: primary.unit ?? '',
                })}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {!isMulti && (
            <div className="text-right">
              <div className="overline">{t('chart.latest')}</div>
              <div className="tabular text-xl font-semibold" data-testid="chart-latest-value">
                {fmt.labValue(lastPoint.value, decimals)}
                <span className="ml-1 text-sm font-normal text-ink-secondary">{primary.unit}</span>
              </div>
            </div>
          )}
          <div className="segmented" role="tablist" aria-label={t('chart.title')}>
            <button
              type="button"
              role="tab"
              aria-selected={view === 'chart'}
              className="segmented-option"
              onClick={() => setView('chart')}
              data-testid="chart-view-toggle"
            >
              {t('chart.chartView')}
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={view === 'table'}
              className="segmented-option"
              onClick={() => setView('table')}
              data-testid="table-view-toggle"
            >
              {t('chart.tableView')}
            </button>
          </div>
        </div>
      </figcaption>

      {/* ---- legend: only for two or more series -------------------------- */}
      {isMulti && (
        <ul className="flex flex-wrap gap-x-4 gap-y-1 px-4 pt-3" data-testid="chart-legend">
          {visible.map((s, index) => (
            <li key={s.analyte_code} className="flex items-center gap-1.5 text-sm text-ink-secondary">
              <span
                aria-hidden="true"
                className="inline-block h-0.5 w-4 rounded-full"
                style={{ background: `rgb(var(${SERIES_VARS[index]}))` }}
              />
              <span className="break-clinical">{s.analyte_name}</span>
              {!normalise && s.unit && <span className="text-ink-muted">({s.unit})</span>}
            </li>
          ))}
        </ul>
      )}

      {view === 'chart' ? (
        <div ref={containerRef} className="chart-surface relative p-4 pt-3">
          {singlePoint && (
            <p className="mb-2 text-sm text-ink-secondary" data-testid="chart-single-point">
              {t('chart.singlePoint')}
            </p>
          )}

          <svg
            width="100%"
            height={HEIGHT}
            viewBox={`0 0 ${width} ${HEIGHT}`}
            role="img"
            aria-labelledby={`${chartId}-title ${chartId}-desc`}
            data-testid="chart-svg"
          >
            <title id={`${chartId}-title`}>{title ?? primary.analyte_name}</title>
            <desc id={`${chartId}-desc`}>{accessibleSummary}</desc>

            <g transform={`translate(${MARGIN.left},${MARGIN.top})`}>
              {/* --- reference band, behind everything --------------------- */}
              {!isMulti && primary.ref_low !== null && primary.ref_high !== null && (
                <>
                  <rect
                    className="chart-reference-band"
                    x={0}
                    y={scales.yScale(primary.ref_high)}
                    width={scales.innerWidth}
                    height={Math.max(scales.yScale(primary.ref_low) - scales.yScale(primary.ref_high), 0)}
                    data-testid="reference-band"
                  />
                  <line
                    className="chart-reference-edge"
                    x1={0}
                    x2={scales.innerWidth}
                    y1={scales.yScale(primary.ref_high)}
                    y2={scales.yScale(primary.ref_high)}
                  />
                  <line
                    className="chart-reference-edge"
                    x1={0}
                    x2={scales.innerWidth}
                    y1={scales.yScale(primary.ref_low)}
                    y2={scales.yScale(primary.ref_low)}
                  />
                </>
              )}

              {/* Normalised compare view: the band is 0-100% by construction */}
              {isMulti && normalise && (
                <rect
                  className="chart-reference-band"
                  x={0}
                  y={scales.yScale(100)}
                  width={scales.innerWidth}
                  height={Math.max(scales.yScale(0) - scales.yScale(100), 0)}
                />
              )}

              {/* --- gridlines -------------------------------------------- */}
              {scales.yTicks.map((tick) => (
                <line
                  key={`grid-${tick}`}
                  className="chart-gridline"
                  x1={0}
                  x2={scales.innerWidth}
                  y1={scales.yScale(tick)}
                  y2={scales.yScale(tick)}
                />
              ))}

              {/* --- axes -------------------------------------------------- */}
              <line className="chart-axis" x1={0} x2={scales.innerWidth} y1={scales.innerHeight} y2={scales.innerHeight} />
              <line className="chart-axis" x1={0} x2={0} y1={0} y2={scales.innerHeight} />

              {scales.yTicks.map((tick) => (
                <text
                  key={`ytick-${tick}`}
                  className="chart-axis-label"
                  x={-8}
                  y={scales.yScale(tick)}
                  textAnchor="end"
                  dominantBaseline="middle"
                >
                  {fmt.number(tick, tick % 1 === 0 ? 0 : decimals)}
                </text>
              ))}

              {scales.xTicks.map((tick) => (
                <text
                  key={`xtick-${tick}`}
                  className="chart-axis-label"
                  x={scales.xScale(tick)}
                  y={scales.innerHeight + 16}
                  textAnchor="middle"
                >
                  {fmt.number(tick, 0)}
                </text>
              ))}

              <text
                className="chart-axis-label"
                x={scales.innerWidth / 2}
                y={scales.innerHeight + 34}
                textAnchor="middle"
              >
                {t('chart.axisX')}
              </text>

              {/* --- crosshair --------------------------------------------- */}
              {hoverDay !== null && (
                <line
                  className="chart-crosshair"
                  x1={scales.xScale(hoverDay)}
                  x2={scales.xScale(hoverDay)}
                  y1={0}
                  y2={scales.innerHeight}
                  data-testid="chart-crosshair"
                />
              )}

              {/* --- series ------------------------------------------------ */}
              {visible.map((s, index) => {
                const colour = `rgb(var(${SERIES_VARS[index]}))`;
                const path = s.points
                  .map((point, i) => {
                    const x = scales.xScale(point.day_offset);
                    const y = scales.yScale(valueOf(s, point.value));
                    return `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`;
                  })
                  .join(' ');

                const last = s.points[s.points.length - 1]!;

                return (
                  <g key={s.analyte_code} data-testid={`series-${s.analyte_code}`}>
                    {s.points.length > 1 && (
                      <path className="chart-series-line" d={path} stroke={colour} />
                    )}

                    {s.points.map((point) => {
                      const x = scales.xScale(point.day_offset);
                      const y = scales.yScale(valueOf(s, point.value));
                      // A critical value gets a hollow marker with a heavy
                      // critical-coloured ring: distinguishable by SHAPE, not
                      // only by colour, so it survives greyscale and CVD.
                      return point.is_critical ? (
                        <circle
                          key={`${s.analyte_code}-${point.day_offset}`}
                          className="chart-marker-critical"
                          cx={x}
                          cy={y}
                          r={5}
                          data-testid="chart-marker-critical"
                        >
                          <title>
                            {t('chart.pointDescription', {
                              day: point.day_offset,
                              value: fmt.labValue(point.value, s.decimals ?? 2),
                              unit: s.unit ?? '',
                              flag: t(`flag.${point.flag}` as never),
                            })}
                          </title>
                        </circle>
                      ) : (
                        <circle
                          key={`${s.analyte_code}-${point.day_offset}`}
                          className="chart-marker"
                          cx={x}
                          cy={y}
                          r={4}
                          fill={colour}
                        >
                          <title>
                            {t('chart.pointDescription', {
                              day: point.day_offset,
                              value: fmt.labValue(point.value, s.decimals ?? 2),
                              unit: s.unit ?? '',
                              flag: t(`flag.${point.flag}` as never),
                            })}
                          </title>
                        </circle>
                      );
                    })}

                    {/* Endpoint label only - never a number on every point. */}
                    <text
                      className="chart-endpoint-label"
                      x={scales.xScale(last.day_offset) + 10}
                      y={scales.yScale(valueOf(s, last.value))}
                      dominantBaseline="middle"
                      data-testid={`endpoint-label-${s.analyte_code}`}
                    >
                      {normalise && isMulti
                        ? `${fmt.number(valueOf(s, last.value), 0)}%`
                        : fmt.labValue(last.value, s.decimals ?? 2)}
                    </text>
                  </g>
                );
              })}

              {/* --- hit area, sized generously for touch ------------------- */}
              <rect
                className="chart-hit-area"
                x={0}
                y={0}
                width={scales.innerWidth}
                height={scales.innerHeight}
                onPointerMove={handlePointer}
                onPointerLeave={() => setHoverDay(null)}
                data-testid="chart-hit-area"
              />
            </g>
          </svg>

          {/* --- tooltip ------------------------------------------------- */}
          {hoveredPoints.length > 0 && hoverDay !== null && (
            <div
              className="chart-tooltip"
              data-testid="chart-tooltip"
              style={{
                // Flips to the left of the crosshair in the right-hand third so
                // it is never clipped by the card edge.
                left: Math.min(
                  MARGIN.left + scales.xScale(hoverDay) + 14,
                  width - 190,
                ),
                top: MARGIN.top + 8,
              }}
              role="status"
            >
              <div className="overline mb-1">{t('labs.day', { day: hoverDay })}</div>
              <ul className="space-y-1">
                {hoveredPoints.map(({ series: s, point }, index) => (
                  <li key={s.analyte_code} className="flex items-center justify-between gap-3">
                    <span className="flex items-center gap-1.5 text-ink-secondary">
                      {isMulti && (
                        <span
                          aria-hidden="true"
                          className="inline-block h-0.5 w-3 rounded-full"
                          style={{ background: `rgb(var(${SERIES_VARS[index]}))` }}
                        />
                      )}
                      {s.analyte_name}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="tabular font-semibold">
                        {fmt.labValue(point.value, s.decimals ?? 2)}
                      </span>
                      <span className="text-ink-muted">{s.unit}</span>
                      <FlagBadge flag={point.flag as ResultFlag} />
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <TrendTable series={visible} />
      )}

      {/* The table is ALWAYS in the DOM for assistive technology, and visually
          hidden when the chart is showing. A chart that is only reachable
          visually is not accessible, whatever its ARIA attributes say. */}
      {view === 'chart' && (
        // `contain: size` keeps this screen-reader copy out of the parent's
        // intrinsic width calculation. Without it the table's min-width leaks
        // into the grid track and pushes the card past the viewport on a
        // narrow screen - which is exactly the mobile German layout bug the
        // Phase 3 suite exists to catch.
        <div className="sr-only" style={{ contain: 'size layout' }}>
          <TrendTable series={visible} />
        </div>
      )}
    </figure>
  );
}

/** The tabular equivalent of the chart. Also the print view. */
export function TrendTable({ series }: { series: AnalyteTrend[] }) {
  const { t, fmt } = useI18n();
  const primary = series[0];
  if (!primary) return null;

  const days = Array.from(
    new Set(series.flatMap((s) => s.points.map((p) => p.day_offset))),
  ).sort((a, b) => a - b);

  return (
    <div className="scroll-x p-4">
      <table className="w-full min-w-[24rem] border-collapse text-sm">
        <caption className="sr-only">
          {t('chart.tableCaption', { analyte: primary.analyte_name })}
        </caption>
        <thead>
          <tr className="border-b border-hairline text-left">
            <th scope="col" className="py-2 pr-4 font-semibold">
              {t('labs.day', { day: '' }).trim()}
            </th>
            {series.map((s) => (
              <th key={s.analyte_code} scope="col" className="py-2 pr-4 font-semibold break-clinical">
                {s.analyte_name}
                {s.unit && <span className="ml-1 font-normal text-ink-muted">({s.unit})</span>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {days.map((day) => (
            <tr key={day} className="border-b border-hairline last:border-0">
              <th scope="row" className="tabular py-2 pr-4 text-left font-normal text-ink-secondary">
                {day}
              </th>
              {series.map((s) => {
                const point = s.points.find((p) => p.day_offset === day);
                return (
                  <td key={s.analyte_code} className="py-2 pr-4">
                    {point ? (
                      <span className="flex items-center gap-2">
                        <span className="tabular">{fmt.labValue(point.value, s.decimals ?? 2)}</span>
                        <FlagBadge flag={point.flag as ResultFlag} />
                      </span>
                    ) : (
                      <span className="text-ink-muted">-</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
