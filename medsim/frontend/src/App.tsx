/**
 * Router and providers.
 *
 * `HashRouter` is deliberately NOT used: the deployment serves the SPA behind
 * nginx with a try_files fallback, so real paths work and are shareable, which
 * matters for bug reports that reference a specific case.
 */

import { Route, Routes } from 'react-router-dom';

import { Shell } from './components/AppChrome';
import { SectionErrorBoundary } from './components/ui';
import { CaseDetailPage } from './pages/CaseDetailPage';
import { DashboardPage } from './pages/DashboardPage';
import { useI18n } from './hooks/useApp';

function NotFoundPage() {
  const { t } = useI18n();
  return (
    <div className="card-padded" data-testid="route-not-found">
      <h1 className="text-xl">{t('errors.notFound')}</h1>
      <p className="mt-1 text-ink-secondary">{t('errors.notFoundHint')}</p>
    </div>
  );
}

export function App() {
  return (
    <Shell>
      <SectionErrorBoundary>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/cases/:identifier" element={<CaseDetailPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </SectionErrorBoundary>
    </Shell>
  );
}
