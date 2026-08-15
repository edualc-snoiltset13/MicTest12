/**
 * Case detail view.
 *
 * Every section is wrapped in its own error boundary. On a clinical review
 * screen, a malformed protocol payload should blank the protocol card and leave
 * the labs, the chart and the diagnosis readable - a whole-page failure throws
 * away information the reader could still have used.
 *
 * Section order follows how a clinician actually reads a case: presentation,
 * then objective data (labs, smear, microbiology, imaging), then the trend that
 * ties the data together, then treatment, then the answer. The diagnosis is
 * last on purpose - this is a teaching corpus, and putting the answer at the
 * top removes the exercise.
 */

import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { api } from '../api/client';
import type {
  CaseDetail,
  Diagnosis,
  LabPanel,
  MicrobiologyReport,
  PeripheralSmear,
  TreatmentProtocol,
} from '../api/types';
import { useAsync } from '../hooks/useAsync';
import { useApp, useI18n } from '../hooks/useApp';
import { pickLocalized } from '../i18n';
import { FlagBadge } from '../components/FlagBadge';
import { LabTrendChart } from '../components/LabTrendChart';
import {
  Chip,
  DifficultyMeter,
  EmptyState,
  ErrorState,
  Field,
  Section,
  SectionErrorBoundary,
  Skeleton,
} from '../components/ui';

export function CaseDetailPage() {
  const { identifier = '' } = useParams();
  const { t, fmt } = useI18n();
  const { locale } = useApp();

  const detail = useAsync((signal) => api.getCase(identifier, { signal }), [identifier]);
  const trends = useAsync((signal) => api.getTrends(identifier, undefined, { signal }), [identifier]);

  if (detail.loading) {
    return (
      <div className="space-y-4" data-testid="case-loading">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (detail.error || !detail.data) {
    return (
      <div className="space-y-4">
        <BackLink />
        <ErrorState error={detail.error} onRetry={detail.reload} />
      </div>
    );
  }

  const record = detail.data;
  const title = pickLocalized(record.title_i18n, locale, record.title);
  const summary = pickLocalized(record.summary_i18n, locale, record.summary);

  return (
    <article className="space-y-8" data-testid="case-detail" data-case-code={record.case_code}>
      <header className="space-y-3">
        <BackLink />

        <div className="flex flex-wrap items-center gap-3">
          <span className="overline tabular">{record.case_code}</span>
          <DifficultyMeter level={record.difficulty} />
          <Chip tone="accent">{t(`discipline.${record.discipline}` as never)}</Chip>
          <span className="text-label text-ink-muted">{t('case.version', { version: record.version })}</span>
        </div>

        <h1 className="max-w-prose text-2xl break-clinical">{title}</h1>
        <p className="max-w-prose text-ink-secondary">{summary}</p>

        <div className="flex flex-wrap gap-1.5">
          {record.tags.map((tag) => (
            <Chip key={tag}>{tag}</Chip>
          ))}
        </div>

        <dl className="grid gap-4 sm:grid-cols-3">
          <Field label={t('case.author')}>{record.author}</Field>
          {record.reviewed_by && <Field label={t('case.reviewedBy')}>{record.reviewed_by}</Field>}
          <Field label={t('case.codes')}>
            <span className="tabular">
              {[...record.icd10_codes, ...record.snomed_codes].join(', ') || t('empty.none')}
            </span>
          </Field>
        </dl>
      </header>

      <SectionErrorBoundary>
        <PatientSection record={record} />
      </SectionErrorBoundary>

      <SectionErrorBoundary>
        <PresentationSection record={record} />
      </SectionErrorBoundary>

      <SectionErrorBoundary>
        <Section id="trends" title={t('case.sections.trends')}>
          {trends.error ? (
            <ErrorState error={trends.error} onRetry={trends.reload} />
          ) : trends.loading ? (
            <Skeleton className="h-64 w-full" />
          ) : trends.data && trends.data.series.length > 0 ? (
            <TrendGallery series={trends.data.series} />
          ) : (
            <EmptyState title={t('chart.noData')} />
          )}
        </Section>
      </SectionErrorBoundary>

      <SectionErrorBoundary>
        <LabsSection panels={record.lab_panels} />
      </SectionErrorBoundary>

      {record.smears.length > 0 && (
        <SectionErrorBoundary>
          <SmearSection smears={record.smears} />
        </SectionErrorBoundary>
      )}

      {record.microbiology.length > 0 && (
        <SectionErrorBoundary>
          <MicrobiologySection reports={record.microbiology} />
        </SectionErrorBoundary>
      )}

      {record.imaging.length > 0 && (
        <SectionErrorBoundary>
          <Section id="imaging" title={t('case.sections.imaging')} count={record.imaging.length}>
            <div className="space-y-3">
              {record.imaging.map((study) => (
                <div key={study.id} className="card-padded" data-testid="imaging-study">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <h3 className="text-base font-semibold">{study.modality}</h3>
                    <span className="text-label text-ink-muted">
                      {study.region} · {t('labs.day', { day: study.day_offset })}
                    </span>
                  </div>
                  <p className="mt-2 max-w-prose text-sm">{study.findings}</p>
                  <p className="mt-2 max-w-prose text-sm font-medium">{study.impression}</p>
                </div>
              ))}
            </div>
          </Section>
        </SectionErrorBoundary>
      )}

      {record.protocols.length > 0 && (
        <SectionErrorBoundary>
          <ProtocolSection protocols={record.protocols} />
        </SectionErrorBoundary>
      )}

      <SectionErrorBoundary>
        <DiagnosisSection diagnoses={record.diagnoses} />
      </SectionErrorBoundary>

      {record.teaching_points.length > 0 && (
        <Section id="teaching" title={t('case.sections.teaching')} count={record.teaching_points.length}>
          <ol className="card-padded max-w-prose list-decimal space-y-3 ps-5 marker:text-ink-muted">
            {record.teaching_points.map((point, index) => (
              <li key={index} className="text-sm leading-relaxed" data-testid="teaching-point">
                {point}
              </li>
            ))}
          </ol>
        </Section>
      )}

      {record.references.length > 0 && (
        <Section id="references" title={t('case.sections.references')}>
          <ul className="card-padded max-w-prose space-y-2 text-sm">
            {record.references.map((reference, index) => (
              <li key={index} className="flex flex-wrap items-baseline gap-2">
                <span className="text-ink-secondary">{reference.citation}</span>
                {reference.type && <Chip>{t(`references.type.${reference.type}` as never)}</Chip>}
              </li>
            ))}
          </ul>
        </Section>
      )}

      <p className="text-label text-ink-muted">
        {t('case.updated', { date: fmt.dateTime(record.updated_at) })}
      </p>
    </article>
  );
}

function BackLink() {
  const { t } = useI18n();
  return (
    <Link to="/" className="btn-ghost -ms-3 inline-flex" data-testid="back-link">
      ← {t('nav.backToCases')}
    </Link>
  );
}

// ---------------------------------------------------------------------------
// Sections
// ---------------------------------------------------------------------------

function PatientSection({ record }: { record: CaseDetail }) {
  const { t, fmt } = useI18n();
  const patient = record.patient;
  if (!patient) return null;

  return (
    <Section id="patient" title={t('case.sections.patient')}>
      <dl className="card-padded grid gap-4 sm:grid-cols-3 lg:grid-cols-4" data-testid="patient-panel">
        <Field label={t('patient.age')}>{t('patient.ageValue', { age: patient.age_years })}</Field>
        <Field label={t('patient.sex')}>{t(`sex.${patient.sex}` as never)}</Field>
        {patient.weight_kg && (
          <Field label={t('patient.weight')}>
            <span className="tabular">{fmt.number(patient.weight_kg, 1)} kg</span>
          </Field>
        )}
        {patient.bmi && (
          <Field label={t('patient.bmi')}>
            <span className="tabular">{fmt.number(patient.bmi, 1)}</span>
          </Field>
        )}
        {patient.ancestry && <Field label={t('patient.ancestry')}>{patient.ancestry}</Field>}
        {patient.pregnancy_status && (
          <Field label={t('patient.pregnancy')}>{patient.pregnancy_status}</Field>
        )}
        {patient.occupation && <Field label={t('patient.occupation')}>{patient.occupation}</Field>}
        {patient.region && <Field label={t('patient.region')}>{patient.region}</Field>}
      </dl>
    </Section>
  );
}

function PresentationSection({ record }: { record: CaseDetail }) {
  const { t } = useI18n();
  const { locale } = useApp();
  const presentation = record.presentation;
  if (!presentation) return null;

  const complaint = pickLocalized(
    presentation.chief_complaint_i18n,
    locale,
    presentation.chief_complaint,
  );

  return (
    <Section id="presentation" title={t('case.sections.presentation')}>
      <div className="space-y-4">
        <div className="card-padded">
          <h3 className="overline">{t('presentation.chiefComplaint')}</h3>
          <p className="mt-1 max-w-prose text-lg leading-snug">{complaint}</p>
          {presentation.history_of_present_illness && (
            <>
              <h3 className="overline mt-4">{t('presentation.history')}</h3>
              <p className="mt-1 max-w-prose text-sm leading-relaxed text-ink-secondary">
                {presentation.history_of_present_illness}
              </p>
            </>
          )}
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          {Object.keys(presentation.vitals).length > 0 && (
            <div className="card-padded">
              <h3 className="overline mb-2">{t('presentation.vitals')}</h3>
              <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {Object.entries(presentation.vitals).map(([key, value]) => (
                  <Field key={key} label={t(`vitals.${key}` as never)}>
                    <span className="tabular">{String(value)}</span>
                  </Field>
                ))}
              </dl>
            </div>
          )}

          {presentation.medications.length > 0 && (
            <div className="card-padded">
              <h3 className="overline mb-2">{t('presentation.medications')}</h3>
              <ul className="space-y-2 text-sm">
                {presentation.medications.map((medication, index) => (
                  <li key={index} className="border-b border-hairline pb-2 last:border-0 last:pb-0">
                    <span className="font-medium">{medication.name}</span>
                    {medication.dose && <span className="text-ink-secondary"> · {medication.dose}</span>}
                    {medication.frequency && (
                      <span className="text-ink-secondary"> · {medication.frequency}</span>
                    )}
                    {medication.notes && (
                      <p className="mt-0.5 text-label text-ink-muted">{medication.notes}</p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {presentation.examination_findings.length > 0 && (
          <div className="card-padded">
            <h3 className="overline mb-2">{t('presentation.examination')}</h3>
            <ul className="max-w-prose list-disc space-y-1 ps-5 text-sm marker:text-ink-muted">
              {presentation.examination_findings.map((finding, index) => (
                <li key={index}>{finding}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-3">
          <ListCard title={t('presentation.pastMedical')} items={presentation.past_medical_history} />
          <ListCard title={t('presentation.allergies')} items={presentation.allergies} />
          <ListCard title={t('presentation.familyHistory')} items={presentation.family_history} />
        </div>
      </div>
    </Section>
  );
}

function ListCard({ title, items }: { title: string; items: string[] }) {
  const { t } = useI18n();
  return (
    <div className="card-padded">
      <h3 className="overline mb-2">{title}</h3>
      {items.length === 0 ? (
        <p className="text-sm text-ink-muted">{t('presentation.none')}</p>
      ) : (
        <ul className="list-disc space-y-1 ps-5 text-sm marker:text-ink-muted">
          {items.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

/**
 * Small multiples: one chart per analyte, each with its own y-axis.
 *
 * This is the alternative to a dual-axis chart. Analytes with different units
 * and magnitudes (TSH in mIU/L against FT4 in pmol/L) cannot share a scale
 * without implying a relationship the data does not support, so each gets its
 * own panel and the reader compares shapes across a shared x-axis.
 */
function TrendGallery({ series }: { series: import('../api/types').AnalyteTrend[] }) {
  const { t } = useI18n();
  const [selected, setSelected] = useState<string[]>([]);

  const plottable = useMemo(() => series.filter((s) => s.points.length >= 1), [series]);
  const compared = plottable.filter((s) => selected.includes(s.analyte_code));

  const toggle = (code: string) => {
    setSelected((current) =>
      current.includes(code)
        ? current.filter((value) => value !== code)
        : current.length >= 3
          ? current
          : [...current, code],
    );
  };

  return (
    <div className="min-w-0 space-y-4">
      <div className="card-padded">
        <h3 className="overline mb-2">{t('chart.compare')}</h3>
        <p className="mb-2 text-sm text-ink-secondary">{t('chart.compareLimit')}</p>
        <div className="flex flex-wrap gap-1.5">
          {plottable.map((s) => (
            <Chip
              key={s.analyte_code}
              onClick={() => toggle(s.analyte_code)}
              active={selected.includes(s.analyte_code)}
              testId="compare-toggle"
            >
              {s.analyte_code}
            </Chip>
          ))}
        </div>
      </div>

      {compared.length > 1 && (
        <LabTrendChart
          series={compared}
          title={t('chart.compare')}
          normalise
          className="lg:col-span-2"
        />
      )}

      <div className="grid min-w-0 gap-4 lg:grid-cols-2">
        {plottable.map((s) => (
          <LabTrendChart key={s.analyte_code} series={[s]} />
        ))}
      </div>
    </div>
  );
}

function LabsSection({ panels }: { panels: LabPanel[] }) {
  const { t, fmt } = useI18n();

  if (panels.length === 0) {
    return (
      <Section id="labs" title={t('case.sections.labs')}>
        <EmptyState title={t('labs.noResults')} />
      </Section>
    );
  }

  return (
    <Section id="labs" title={t('case.sections.labs')} count={panels.length}>
      <div className="space-y-4">
        {panels.map((panel) => (
          <div key={panel.id} className="card overflow-hidden" data-testid="lab-panel">
            <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-hairline p-4 pb-3">
              <h3 className="text-base font-semibold break-clinical">{panel.panel_name}</h3>
              <span className="text-label text-ink-muted tabular">
                {panel.day_offset === 0
                  ? t('labs.dayZero')
                  : t('labs.day', { day: panel.day_offset })}{' '}
                · {fmt.dateTime(panel.collected_at)}
              </span>
            </div>

            {panel.comment && (
              <p className="border-b border-hairline bg-surface-sunken px-4 py-2 text-sm text-ink-secondary">
                {panel.comment}
              </p>
            )}

            {/* The table scrolls inside its own container so the page body
                never scrolls horizontally on a phone. */}
            <div className="scroll-x">
              <table className="w-full min-w-[36rem] border-collapse text-sm">
                <thead>
                  <tr className="border-b border-hairline text-left">
                    <th scope="col" className="px-4 py-2 font-semibold">{t('labs.analyte')}</th>
                    <th scope="col" className="px-4 py-2 text-right font-semibold">{t('labs.value')}</th>
                    <th scope="col" className="px-4 py-2 font-semibold">{t('labs.unit')}</th>
                    <th scope="col" className="px-4 py-2 font-semibold">{t('labs.referenceRange')}</th>
                    <th scope="col" className="px-4 py-2 font-semibold">{t('labs.flag')}</th>
                  </tr>
                </thead>
                <tbody>
                  {panel.results.map((result) => (
                    <tr
                      key={result.id}
                      className={`border-b border-hairline last:border-0 ${
                        result.is_critical ? 'bg-critical-wash' : ''
                      }`}
                      data-testid="lab-result-row"
                      data-analyte={result.analyte_code}
                    >
                      <th scope="row" className="px-4 py-2 text-left font-normal break-clinical">
                        {result.analyte_name}
                        {result.interference_note && (
                          <details className="mt-1">
                            <summary className="cursor-pointer text-label text-accent">
                              {t('labs.note')}
                            </summary>
                            <p className="mt-1 max-w-prose text-label text-ink-secondary">
                              {result.interference_note}
                            </p>
                          </details>
                        )}
                      </th>
                      <td className="tabular px-4 py-2 text-right font-medium">
                        {result.value_numeric !== null
                          ? fmt.labValue(result.value_numeric, decimalsFor(result.value_numeric))
                          : result.value_text}
                      </td>
                      <td className="px-4 py-2 text-ink-secondary">{result.unit ?? ''}</td>
                      <td className="tabular px-4 py-2 text-ink-secondary">
                        {formatRange(result.ref_low, result.ref_high, result.ref_text, fmt)}
                      </td>
                      <td className="px-4 py-2">
                        <FlagBadge flag={result.flag} />
                        {result.is_critical && (
                          <span className="sr-only">{t('labs.criticalWarning')}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}

/**
 * Chooses a display precision from the magnitude of the value itself.
 *
 * The API supplies authoritative per-analyte precision through the reference
 * intervals; this is the fallback for results whose analyte has no registered
 * interval. A TSH of 0.005 must not render as "0.01".
 */
function decimalsFor(value: number): number {
  const magnitude = Math.abs(value);
  if (magnitude === 0) return 0;
  if (magnitude < 0.1) return 3;
  if (magnitude < 10) return 2;
  if (magnitude < 100) return 1;
  return 0;
}

function formatRange(
  low: number | null,
  high: number | null,
  text: string | null,
  fmt: ReturnType<typeof useI18n>['fmt'],
): string {
  if (text) return text;
  if (low !== null && high !== null) {
    return `${fmt.labValue(low, decimalsFor(low))} – ${fmt.labValue(high, decimalsFor(high))}`;
  }
  if (high !== null) return `< ${fmt.labValue(high, decimalsFor(high))}`;
  if (low !== null) return `> ${fmt.labValue(low, decimalsFor(low))}`;
  return '—';
}

function SmearSection({ smears }: { smears: PeripheralSmear[] }) {
  const { t, fmt } = useI18n();
  const { locale } = useApp();

  return (
    <Section id="smear" title={t('case.sections.smear')} count={smears.length}>
      <div className="space-y-4">
        {smears.map((smear) => (
          <div key={smear.id} className="card-padded" data-testid="smear-report">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="text-base font-semibold">
                {t('labs.day', { day: smear.day_offset })}
              </h3>
              <span className="text-label text-ink-muted">
                {smear.stain}
                {smear.reported_by && ` · ${smear.reported_by}`}
              </span>
            </div>

            {smear.schistocyte_percent !== null && (
              <div className="mt-3 rounded-control bg-surface-sunken p-3">
                <div className="overline">{t('smear.schistocytes')}</div>
                <div className="tabular mt-0.5 text-lg font-semibold">
                  {t('smear.schistocyteValue', {
                    value: fmt.number(smear.schistocyte_percent, 1),
                  })}
                </div>
                <p className="mt-1 text-label text-ink-secondary">{t('smear.schistocyteThreshold')}</p>
              </div>
            )}

            <div className="mt-4 grid gap-4 lg:grid-cols-3">
              <MorphologyList title={t('smear.redCells')} items={smear.red_cell_morphology} />
              <MorphologyList title={t('smear.whiteCells')} items={smear.white_cell_morphology} />
              <MorphologyList title={t('smear.platelets')} items={smear.platelet_morphology} />
            </div>

            {smear.narrative && (
              <div className="mt-4">
                <h4 className="overline mb-1">{t('smear.narrative')}</h4>
                <p className="max-w-prose text-sm leading-relaxed">
                  {pickLocalized(smear.narrative_i18n, locale, smear.narrative)}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
    </Section>
  );
}

function MorphologyList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <h4 className="overline mb-1">{title}</h4>
      <ul className="list-disc space-y-1 ps-5 text-sm marker:text-ink-muted">
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function MicrobiologySection({ reports }: { reports: MicrobiologyReport[] }) {
  const { t, fmt } = useI18n();

  return (
    <Section id="microbiology" title={t('case.sections.microbiology')} count={reports.length}>
      <div className="space-y-4">
        {reports.map((report) => (
          <div key={report.id} className="card-padded" data-testid="microbiology-report">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="text-base font-semibold break-clinical">{report.specimen_type}</h3>
              <span className="text-label text-ink-muted">
                {t('labs.day', { day: report.day_offset })}
                {report.site && ` · ${report.site}`}
              </span>
            </div>

            {(report.bacterial_index !== null || report.morphological_index !== null) && (
              <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                {report.bacterial_index !== null && (
                  <div className="rounded-control bg-surface-sunken p-3">
                    <dt className="overline">{t('microbiology.bacterialIndex')}</dt>
                    <dd className="tabular mt-0.5 text-lg font-semibold">
                      {fmt.number(report.bacterial_index, 1)}
                    </dd>
                    <p className="mt-1 text-label text-ink-secondary">
                      {t('microbiology.bacterialIndexHelp')}
                    </p>
                  </div>
                )}
                {report.morphological_index !== null && (
                  <div className="rounded-control bg-surface-sunken p-3">
                    <dt className="overline">{t('microbiology.morphologicalIndex')}</dt>
                    <dd className="tabular mt-0.5 text-lg font-semibold">
                      {fmt.number(report.morphological_index, 1)}%
                    </dd>
                    <p className="mt-1 text-label text-ink-secondary">
                      {t('microbiology.morphologicalIndexHelp')}
                    </p>
                  </div>
                )}
              </dl>
            )}

            {report.microscopy && <p className="mt-3 max-w-prose text-sm">{report.microscopy}</p>}

            {report.molecular_findings.length > 0 && (
              <div className="mt-4">
                <h4 className="overline mb-2">{t('microbiology.molecular')}</h4>
                <div className="scroll-x">
                  <table className="w-full min-w-[32rem] border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-hairline text-left">
                        <th scope="col" className="py-2 pe-4 font-semibold">{t('microbiology.target')}</th>
                        <th scope="col" className="py-2 pe-4 font-semibold">{t('microbiology.result')}</th>
                        <th scope="col" className="py-2 font-semibold">{t('microbiology.interpretation')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.molecular_findings.map((finding, index) => (
                        <tr key={index} className="border-b border-hairline last:border-0">
                          <th scope="row" className="py-2 pe-4 text-left font-mono text-label">
                            {finding.target}
                          </th>
                          <td className="py-2 pe-4 break-clinical">{finding.result}</td>
                          <td className="py-2 text-ink-secondary">{finding.interpretation ?? ''}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {report.susceptibility.length > 0 && (
              <div className="mt-4">
                <h4 className="overline mb-2">{t('microbiology.susceptibility')}</h4>
                <ul className="flex flex-wrap gap-2" data-testid="susceptibility-list">
                  {report.susceptibility.map((entry, index) => {
                    const resistant = /resistant/i.test(entry.result);
                    return (
                      <li
                        key={index}
                        className={`flex items-center gap-1.5 rounded-control border px-2 py-1 text-sm ${
                          resistant
                            ? 'border-critical/40 bg-critical-wash'
                            : 'border-good/40 bg-good-wash'
                        }`}
                        data-resistant={resistant}
                      >
                        {/* Shape + text, not colour alone. */}
                        <span aria-hidden="true">{resistant ? '✕' : '✓'}</span>
                        <span className="font-medium">{entry.agent}</span>
                        <span className="text-ink-secondary">{entry.result}</span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {report.interpretation && (
              <p className="mt-4 max-w-prose rounded-control bg-accent-wash p-3 text-sm">
                {report.interpretation}
              </p>
            )}
          </div>
        ))}
      </div>
    </Section>
  );
}

function ProtocolSection({ protocols }: { protocols: TreatmentProtocol[] }) {
  const { t } = useI18n();
  const { locale } = useApp();

  return (
    <Section id="protocol" title={t('case.sections.protocol')} count={protocols.length}>
      <div className="space-y-4">
        {protocols.map((protocol) => (
          <div key={protocol.id} className="card-padded" data-testid="treatment-protocol">
            <h3 className="text-lg font-semibold break-clinical">
              {pickLocalized(protocol.name_i18n, locale, protocol.name)}
            </h3>

            <dl className="mt-3 grid gap-3 sm:grid-cols-3">
              {protocol.guideline_source && (
                <Field label={t('protocol.guideline')} className="sm:col-span-2">
                  {protocol.guideline_source}
                </Field>
              )}
              <Field label={t('protocol.duration')}>
                {protocol.duration_months === null
                  ? t('protocol.durationIndefinite')
                  : t('protocol.durationMonths', { count: protocol.duration_months })}
              </Field>
            </dl>

            {protocol.indication && (
              <p className="mt-3 max-w-prose text-sm text-ink-secondary">{protocol.indication}</p>
            )}

            {protocol.regimen.length > 0 && (
              <div className="mt-4">
                <h4 className="overline mb-2">{t('protocol.regimen')}</h4>
                <div className="scroll-x">
                  <table className="w-full min-w-[40rem] border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-hairline text-left">
                        <th scope="col" className="py-2 pe-4 font-semibold">{t('protocol.agent')}</th>
                        <th scope="col" className="py-2 pe-4 font-semibold">{t('protocol.dose')}</th>
                        <th scope="col" className="py-2 pe-4 font-semibold">{t('protocol.route')}</th>
                        <th scope="col" className="py-2 pe-4 font-semibold">{t('protocol.frequency')}</th>
                        <th scope="col" className="py-2 font-semibold">{t('protocol.duration')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {protocol.regimen.map((step, index) => (
                        <tr key={index} className="border-b border-hairline last:border-0" data-testid="regimen-step">
                          <th scope="row" className="py-2 pe-4 text-left font-medium break-clinical">
                            {step.agent}
                            {step.notes && (
                              <p className="mt-0.5 max-w-prose text-label font-normal text-ink-secondary">
                                {step.notes}
                              </p>
                            )}
                          </th>
                          <td className="py-2 pe-4 tabular">{step.dose}</td>
                          <td className="py-2 pe-4 text-ink-secondary">{step.route}</td>
                          <td className="py-2 pe-4 text-ink-secondary">{step.frequency}</td>
                          <td className="py-2 text-ink-secondary">{step.duration ?? ''}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="mt-4 grid gap-4 lg:grid-cols-3">
              <ListCard title={t('protocol.monitoring')} items={protocol.monitoring} />
              <ListCard title={t('protocol.contraindications')} items={protocol.contraindications} />
              <ListCard title={t('protocol.adverseEffects')} items={protocol.adverse_effects} />
            </div>

            {protocol.notes && (
              <p className="mt-4 max-w-prose rounded-control bg-surface-sunken p-3 text-sm">
                {protocol.notes}
              </p>
            )}
          </div>
        ))}
      </div>
    </Section>
  );
}

function DiagnosisSection({ diagnoses }: { diagnoses: Diagnosis[] }) {
  const { t, fmt } = useI18n();
  const { locale } = useApp();
  const [revealed, setRevealed] = useState(false);

  if (diagnoses.length === 0) {
    return (
      <Section id="diagnosis" title={t('case.sections.diagnosis')}>
        <EmptyState title={t('diagnosis.none')} />
      </Section>
    );
  }

  const primary = diagnoses.find((d) => d.is_primary);
  const differential = diagnoses.filter((d) => !d.is_primary);

  // This is a teaching corpus, so the answer is behind one deliberate click.
  // Not a security control - just enough friction that a reader has to decide
  // to see it rather than absorbing it while scrolling past.
  if (!revealed) {
    return (
      <Section id="diagnosis" title={t('case.sections.diagnosis')}>
        <div className="card-padded text-center">
          <button
            type="button"
            className="btn-primary"
            onClick={() => setRevealed(true)}
            data-testid="reveal-diagnosis"
          >
            {t('actions.expand')} · {t('diagnosis.title')}
          </button>
        </div>
      </Section>
    );
  }

  return (
    <Section
      id="diagnosis"
      title={t('case.sections.diagnosis')}
      actions={
        <button type="button" className="btn-ghost text-sm" onClick={() => setRevealed(false)}>
          {t('actions.collapse')}
        </button>
      }
    >
      <div className="space-y-4" data-testid="diagnosis-panel">
        {primary && (
          <div className="card-padded border-accent/40 bg-accent-wash" data-testid="primary-diagnosis">
            <div className="overline">{t('diagnosis.primary')}</div>
            <h3 className="mt-1 text-lg font-semibold break-clinical">
              {pickLocalized(primary.label_i18n, locale, primary.label)}
            </h3>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <Chip tone="accent">{t(`certainty.${primary.certainty}` as never)}</Chip>
              {primary.likelihood !== null && (
                <span className="text-label text-ink-secondary tabular">
                  {t('diagnosis.likelihood')}: {fmt.percent(primary.likelihood, 0)}
                </span>
              )}
              {primary.icd10 && (
                <span className="text-label text-ink-muted tabular">
                  {t('diagnosis.icd10')} {primary.icd10}
                </span>
              )}
            </div>
            {primary.discriminator && (
              <>
                <h4 className="overline mt-3">{t('diagnosis.discriminator')}</h4>
                <p className="mt-1 max-w-prose text-sm">{primary.discriminator}</p>
              </>
            )}
            {primary.supporting_evidence.length > 0 && (
              <>
                <h4 className="overline mt-3">{t('diagnosis.supporting')}</h4>
                <ul className="mt-1 max-w-prose list-disc space-y-1 ps-5 text-sm marker:text-ink-muted">
                  {primary.supporting_evidence.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}

        {differential.length > 0 && (
          <div>
            <h3 className="overline mb-2">{t('diagnosis.differential')}</h3>
            <div className="space-y-3">
              {differential.map((diagnosis) => (
                <div key={diagnosis.id} className="card-padded" data-testid="differential-diagnosis">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <h4 className="font-semibold break-clinical">
                      {pickLocalized(diagnosis.label_i18n, locale, diagnosis.label)}
                    </h4>
                    <div className="flex items-center gap-2">
                      <Chip>{t(`certainty.${diagnosis.certainty}` as never)}</Chip>
                      {diagnosis.likelihood !== null && (
                        <span className="text-label text-ink-muted tabular">
                          {fmt.percent(diagnosis.likelihood, 0)}
                        </span>
                      )}
                    </div>
                  </div>
                  {diagnosis.discriminator && (
                    <p className="mt-2 max-w-prose text-sm text-ink-secondary">
                      {diagnosis.discriminator}
                    </p>
                  )}
                  {diagnosis.refuting_evidence.length > 0 && (
                    <>
                      <h5 className="overline mt-3">{t('diagnosis.refuting')}</h5>
                      <ul className="mt-1 max-w-prose list-disc space-y-1 ps-5 text-sm marker:text-ink-muted">
                        {diagnosis.refuting_evidence.map((item, index) => (
                          <li key={index}>{item}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Section>
  );
}
