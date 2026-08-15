/**
 * Dashboard: the filterable case grid.
 *
 * Layout decisions:
 *  - Filters occupy a single column on the left at >=1024px and collapse into a
 *    disclosure above the grid below that. A filter rail that becomes a
 *    horizontal scroller on a phone is unusable with a thumb.
 *  - The grid keeps the previous results on screen while refetching, with a
 *    subdued opacity, rather than flashing to skeletons on every keystroke.
 *  - Filter state lives in the URL. A tester reporting "no results with these
 *    filters" can paste a link that reproduces it exactly.
 */

import { useCallback, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { api } from '../api/client';
import type { CaseQuery, CaseSummary, Discipline, SortField } from '../api/types';
import { useAsync, useDebounced } from '../hooks/useAsync';
import { useApp, useI18n } from '../hooks/useApp';
import { pickLocalized } from '../i18n';
import {
  CaseCardSkeleton,
  Chip,
  DifficultyMeter,
  EmptyState,
  ErrorState,
  LiveRegion,
  StatTile,
} from '../components/ui';

const DISCIPLINES: Discipline[] = [
  'chemical_pathology',
  'hematology',
  'microbiology',
  'pharmacology',
];

const SORT_FIELDS: SortField[] = ['case_code', 'title', 'difficulty', 'updated_at', 'discipline'];

export function DashboardPage() {
  const { t, fmt } = useI18n();
  const { locale } = useApp();
  const [params, setParams] = useSearchParams();

  const search = params.get('q') ?? '';
  const discipline = (params.get('discipline') ?? '') as Discipline | '';
  const difficulty = params.get('difficulty') ?? '';
  const tag = params.get('tag') ?? '';
  const sortBy = (params.get('sort') ?? 'case_code') as SortField;
  const sortDir = (params.get('dir') ?? 'asc') as 'asc' | 'desc';

  const debouncedSearch = useDebounced(search, 250);

  const query = useMemo<CaseQuery>(
    () => ({
      limit: 100,
      search: debouncedSearch || undefined,
      discipline: discipline || undefined,
      difficulty: difficulty ? Number(difficulty) : undefined,
      tag: tag || undefined,
      sort_by: sortBy,
      sort_dir: sortDir,
    }),
    [debouncedSearch, discipline, difficulty, tag, sortBy, sortDir],
  );

  const cases = useAsync((signal) => api.listCases(query, { signal }), [query]);
  const stats = useAsync((signal) => api.getStats({ signal }), []);

  const update = useCallback(
    (key: string, value: string) => {
      const next = new URLSearchParams(params);
      if (value) next.set(key, value);
      else next.delete(key);
      // Preserve the language when filters change; it lives in the same
      // query string and would otherwise be dropped.
      setParams(next, { replace: true });
    },
    [params, setParams],
  );

  const clearAll = useCallback(() => {
    const next = new URLSearchParams();
    const lang = params.get('lang');
    if (lang) next.set('lang', lang);
    setParams(next, { replace: true });
  }, [params, setParams]);

  const activeFilterCount = [search, discipline, difficulty, tag].filter(Boolean).length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl">{t('dashboard.title')}</h1>
        <p className="mt-1 max-w-prose text-ink-secondary">{t('dashboard.subtitle')}</p>
      </div>

      {/* --- corpus statistics ------------------------------------------- */}
      {stats.data && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4" data-testid="stats-row">
          <StatTile label={t('dashboard.stats.totalCases')} value={fmt.number(stats.data.total_cases, 0)} />
          <StatTile label={t('dashboard.stats.totalPanels')} value={fmt.number(stats.data.total_panels, 0)} />
          <StatTile
            label={t('dashboard.stats.totalResults')}
            value={fmt.number(stats.data.total_lab_results, 0)}
          />
          <StatTile
            label={t('dashboard.stats.disciplines')}
            value={fmt.number(Object.keys(stats.data.by_discipline).length, 0)}
          />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-dashboard">
        {/* --- filter rail ----------------------------------------------- */}
        <aside className="lg:sticky lg:top-20 lg:self-start" aria-label={t('filters.title')}>
          <div className="card-padded space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg">{t('filters.title')}</h2>
              {activeFilterCount > 0 && (
                <button type="button" className="btn-ghost text-sm" onClick={clearAll} data-testid="clear-filters">
                  {t('actions.clearAll')}
                </button>
              )}
            </div>

            <div>
              <label htmlFor="filter-search" className="overline mb-1 block">
                {t('actions.search')}
              </label>
              <input
                id="filter-search"
                type="search"
                className="input"
                placeholder={t('filters.searchPlaceholder')}
                aria-label={t('filters.searchLabel')}
                value={search}
                onChange={(event) => update('q', event.target.value)}
                data-testid="search-input"
              />
            </div>

            <div>
              <label htmlFor="filter-discipline" className="overline mb-1 block">
                {t('filters.discipline')}
              </label>
              <select
                id="filter-discipline"
                className="input"
                value={discipline}
                onChange={(event) => update('discipline', event.target.value)}
                data-testid="discipline-filter"
              >
                <option value="">{t('filters.all')}</option>
                {DISCIPLINES.map((value) => (
                  <option key={value} value={value}>
                    {t(`discipline.${value}` as never)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="filter-difficulty" className="overline mb-1 block">
                {t('filters.difficulty')}
              </label>
              <select
                id="filter-difficulty"
                className="input"
                value={difficulty}
                onChange={(event) => update('difficulty', event.target.value)}
                data-testid="difficulty-filter"
              >
                <option value="">{t('filters.all')}</option>
                {[1, 2, 3, 4, 5].map((level) => (
                  <option key={level} value={level}>
                    {t(`difficulty.${level}` as never)}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label htmlFor="filter-sort" className="overline mb-1 block">
                  {t('filters.sortBy')}
                </label>
                <select
                  id="filter-sort"
                  className="input"
                  value={sortBy}
                  onChange={(event) => update('sort', event.target.value)}
                  data-testid="sort-field"
                >
                  {SORT_FIELDS.map((field) => (
                    <option key={field} value={field}>
                      {t(`sort.${field}` as never)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="filter-dir" className="overline mb-1 block">
                  {t('filters.sortDirection')}
                </label>
                <select
                  id="filter-dir"
                  className="input"
                  value={sortDir}
                  onChange={(event) => update('dir', event.target.value)}
                  data-testid="sort-direction"
                >
                  <option value="asc">{t('filters.ascending')}</option>
                  <option value="desc">{t('filters.descending')}</option>
                </select>
              </div>
            </div>

            {tag && (
              <div>
                <span className="overline mb-1 block">{t('filters.tag')}</span>
                <Chip onClick={() => update('tag', '')} active testId="active-tag-filter">
                  {tag} ✕
                </Chip>
              </div>
            )}

            {activeFilterCount > 0 && (
              <p className="text-sm text-ink-secondary" data-testid="active-filter-count">
                {t('filters.activeCount', { count: activeFilterCount })}
              </p>
            )}
          </div>
        </aside>

        {/* --- results ---------------------------------------------------- */}
        <div>
          <div className="mb-3 flex items-baseline justify-between gap-3">
            <p className="text-sm text-ink-secondary" data-testid="result-count">
              {cases.data
                ? activeFilterCount > 0
                  ? t('dashboard.resultCountFiltered', {
                      count: cases.data.meta.returned,
                      total: stats.data?.total_cases ?? cases.data.meta.total,
                    })
                  : t('dashboard.resultCount', { count: cases.data.meta.total })
                : t('dashboard.loading')}
            </p>
          </div>

          <LiveRegion
            message={cases.data ? t('dashboard.resultCount', { count: cases.data.meta.total }) : ''}
          />

          {cases.error ? (
            <ErrorState error={cases.error} onRetry={cases.reload} />
          ) : cases.loading ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }, (_, index) => (
                <CaseCardSkeleton key={index} />
              ))}
            </div>
          ) : cases.data && cases.data.items.length === 0 ? (
            <EmptyState
              title={t('dashboard.noResults')}
              hint={t('dashboard.noResultsHint')}
              action={
                <button type="button" className="btn-secondary" onClick={clearAll}>
                  {t('actions.clearAll')}
                </button>
              }
            />
          ) : (
            <ul
              className={`grid gap-4 sm:grid-cols-2 xl:grid-cols-3 ${
                cases.refreshing ? 'opacity-60 transition-opacity' : ''
              }`}
              data-testid="case-grid"
              aria-busy={cases.refreshing}
            >
              {cases.data?.items.map((item) => (
                <li key={item.id}>
                  <CaseCard caseSummary={item} locale={locale} onTagClick={(value) => update('tag', value)} />
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

function CaseCard({
  caseSummary,
  locale,
  onTagClick,
}: {
  caseSummary: CaseSummary;
  locale: string;
  onTagClick: (tag: string) => void;
}) {
  const { t, fmt } = useI18n();
  const title = pickLocalized(caseSummary.title_i18n, locale as never, caseSummary.title);
  const summary = pickLocalized(caseSummary.summary_i18n, locale as never, caseSummary.summary);

  return (
    <article
      className="card relative flex h-full min-w-0 flex-col p-4 transition-shadow hover:shadow-raised"
      data-testid="case-card"
      data-case-code={caseSummary.case_code}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="overline tabular">{caseSummary.case_code}</span>
        <DifficultyMeter level={caseSummary.difficulty} />
      </div>

      <h3 className="mt-2 text-base font-semibold leading-snug">
        {/* The whole card is not a link: the tag chips inside it are separate
            controls, and nesting interactive elements breaks keyboard order. */}
        <Link
          to={`/cases/${caseSummary.case_code}`}
          className="break-clinical text-ink no-underline after:absolute after:inset-0 hover:text-accent"
          data-testid="case-link"
        >
          {title}
        </Link>
      </h3>

      <p className="mt-2 line-clamp-3 flex-1 text-sm text-ink-secondary">{summary}</p>

      <div className="relative z-10 mt-3 flex flex-wrap items-center gap-1.5">
        <Chip tone="accent">{t(`discipline.${caseSummary.discipline}` as never)}</Chip>
        {caseSummary.tags.slice(0, 3).map((tag) => (
          <Chip key={tag} onClick={() => onTagClick(tag)} testId="case-tag">
            {tag}
          </Chip>
        ))}
      </div>

      <p className="mt-3 text-label text-ink-muted">
        {t('case.updated', { date: fmt.date(caseSummary.updated_at) })}
      </p>
    </article>
  );
}
