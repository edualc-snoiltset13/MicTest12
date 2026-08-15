/// <reference types="cypress" />

import { expectUncaughtException } from '../support/e2e';

/**
 * Spec 04 - Network interception. Edge cases 39-50.
 *
 * These simulate what a man-in-the-middle proxy (Charles, Proxyman, mitmproxy)
 * does to an application: rewriting bodies, breaking TLS, dropping connections,
 * throttling and stalling. The equivalent real-proxy configurations live in
 * `qa/proxy/` for manual testing against a device; this spec reproduces the
 * same failure modes deterministically in CI, where no proxy is installed.
 *
 * The standard the application is held to: **every** one of these failures must
 * produce a distinguishable, actionable error state. Not a blank page, not a
 * spinner forever, and not an unhandled promise rejection.
 */

describe('04 - Network interception and resilience', () => {
  it('EC-39: a 500 renders a server-error state with the request id', () => {
    cy.intercept('GET', '**/api/v1/cases?*', {
      statusCode: 500,
      body: {
        type: 'https://medsimqa.dev/errors/500',
        title: 'Internal server error',
        status: 500,
        detail: 'Injected by the QA suite.',
        instance: '/api/v1/cases',
        errors: [],
        request_id: 'qa-injected-500',
      },
    }).as('serverError');

    cy.visitLocale('/', 'en');
    cy.wait('@serverError');

    cy.get('[data-testid="error-state"]')
      .should('be.visible')
      .and('have.attr', 'data-error-kind', 'status-500');
    cy.get('[data-testid="error-state"]').should('contain', 'qa-injected-500');
    cy.get('[data-testid="error-retry"]').should('be.visible');
  });

  it('EC-40: a 503 with an RFC-7807 body is rendered from that body', () => {
    cy.intercept('GET', '**/api/v1/cases?*', {
      statusCode: 503,
      fixture: 'rfc7807-error.json',
    }).as('unavailable');

    cy.visitLocale('/', 'en');
    cy.wait('@unavailable');
    cy.get('[data-testid="error-state"]').should('contain', 'fixture-request-id-0001');
  });

  it('EC-41: malformed JSON in a 2xx is caught, not thrown', () => {
    // The signature of a rewriting proxy: the status says success, the body is
    // not the JSON it claims. Applications that call response.json() without a
    // guard die here with an unhandled SyntaxError.
    cy.intercept('GET', '**/api/v1/cases?*', {
      statusCode: 200,
      headers: { 'content-type': 'application/json' },
      body: '{"meta":{"total":25},"items":[{"id":1,,',
    }).as('malformed');

    cy.visitLocale('/', 'en');
    cy.wait('@malformed');

    cy.get('[data-testid="error-state"]')
      .should('be.visible')
      .and('have.attr', 'data-error-kind', 'parse');
    // The hint must name the likely cause, or the error is mystifying.
    cy.get('[data-testid="error-state"]').should('contain', 'proxy');
  });

  it('EC-42: a truncated response body is treated as a parse failure', () => {
    // A dropped packet mid-transfer: valid JSON that simply stops.
    cy.intercept('GET', '**/api/v1/cases?*', {
      statusCode: 200,
      headers: { 'content-type': 'application/json' },
      body: '{"meta":{"total":25,"limit":50,"offset":0,"returned":25,"has_m',
    }).as('truncated');

    cy.visitLocale('/', 'en');
    cy.wait('@truncated');
    cy.get('[data-testid="error-state"]').should('have.attr', 'data-error-kind', 'parse');
  });

  it('EC-43: an HTML captive-portal page returned as JSON does not crash the app', () => {
    // Hotel wifi and corporate proxies do this: a 200 whose body is a login
    // page. It is the single most common real-world cause of this failure.
    cy.intercept('GET', '**/api/v1/cases?*', {
      statusCode: 200,
      headers: { 'content-type': 'text/html' },
      body: '<!doctype html><html><body><h1>Sign in to continue</h1></body></html>',
    }).as('captivePortal');

    cy.visitLocale('/', 'en');
    cy.wait('@captivePortal');
    cy.get('[data-testid="error-state"]').should('have.attr', 'data-error-kind', 'parse');
    // The raw body must be inspectable, so a tester can see it was HTML.
    cy.get('[data-testid="error-state"]').find('details').should('exist');
  });

  it('EC-44: an empty 200 body does not render an empty dashboard as success', () => {
    cy.intercept('GET', '**/api/v1/cases?*', {
      statusCode: 200,
      headers: { 'content-type': 'application/json' },
      body: '',
    }).as('emptyBody');

    cy.visitLocale('/', 'en');
    cy.wait('@emptyBody');
    // Either an error state or an explicit empty state - but never a silent
    // blank grid that looks like "there are no cases".
    cy.get('[data-testid="error-state"], [data-testid="empty-state"]').should('exist');
  });

  it('EC-45: a dropped connection is reported as a network error', () => {
    // forceNetworkError is Cypress's equivalent of a connection reset. In the
    // browser this is indistinguishable from an untrusted TLS certificate -
    // which is exactly what an intercepting proxy without its CA installed
    // produces - so the application must not claim to know which it was.
    expectUncaughtException();
    cy.intercept('GET', '**/api/v1/cases?*', { forceNetworkError: true }).as('dropped');

    cy.visitLocale('/', 'en');
    cy.get('[data-testid="error-state"]')
      .should('be.visible')
      .and('have.attr', 'data-error-kind', 'network');
  });

  it('EC-46: an SSL/TLS failure surfaces the same network error, not a blank page', () => {
    // Simulates the proxy-CA-not-installed case specifically. The assertion is
    // that the UI degrades identically and offers a retry, because there is
    // nothing more the browser can tell us.
    expectUncaughtException();
    cy.intercept('GET', '**/api/v1/cases?*', { forceNetworkError: true });

    cy.visitLocale('/', 'en');
    cy.get('[data-testid="error-state"]').should('be.visible');
    cy.get('[data-testid="error-retry"]').should('be.visible');
    // And nothing was left half-rendered.
    cy.get('[data-testid="case-card"]').should('not.exist');
  });

  it('EC-47: a slow response keeps the loading state, then resolves', () => {
    cy.intercept('GET', '**/api/v1/cases?*', (request) => {
      request.on('response', (response) => {
        response.setDelay(3000);
      });
    }).as('slow');

    cy.visitLocale('/', 'en');
    // Skeletons, not a blank page, while waiting.
    cy.get('[data-testid="case-skeleton"]').should('exist');
    cy.wait('@slow');
    cy.get('[data-testid="case-card"]', { timeout: 10000 }).should('have.length', 25);
    cy.get('[data-testid="case-skeleton"]').should('not.exist');
  });

  it('EC-48: retry after a transient failure recovers without a reload', () => {
    let call = 0;
    cy.intercept('GET', '**/api/v1/cases?*', (request) => {
      call += 1;
      if (call === 1) {
        request.reply({ statusCode: 503, body: { title: 'Unavailable', status: 503, detail: '', type: '', instance: null, errors: [], request_id: 'retry-1' } });
      } else {
        request.continue();
      }
    }).as('flaky');

    cy.visitLocale('/', 'en');
    cy.get('[data-testid="error-state"]').should('be.visible');
    cy.get('[data-testid="error-retry"]').click();
    cy.get('[data-testid="case-card"]').should('have.length', 25);
    cy.get('[data-testid="error-state"]').should('not.exist');
  });

  it('EC-49: a stale in-flight response cannot overwrite newer filter results', () => {
    // The classic React data race. Filter A is slow, filter B is fast; if the
    // client does not abort A, its late response repaints the grid with the
    // wrong rows and the UI silently disagrees with its own controls.
    cy.intercept('GET', '**/api/v1/cases?*', (request) => {
      // Delay only the unfiltered request; let the filtered one through fast.
      if (!request.url.includes('discipline=')) {
        request.on('response', (response) => response.setDelay(2500));
      }
    }).as('raced');

    cy.visitLocale('/', 'en');
    cy.get('[data-testid="discipline-filter"]').select('pharmacology');

    // Pharmacology has 3 cases. If the stale 25-case response lands after, the
    // count reverts and this fails.
    cy.get('[data-testid="case-card"]', { timeout: 10000 }).should('have.length', 3);
    cy.wait(3000);
    cy.get('[data-testid="case-card"]').should('have.length', 3);
  });

  it('EC-50: a partial API failure degrades one section, not the page', () => {
    // Stats fail, cases succeed. The dashboard must still list cases.
    cy.intercept('GET', '**/api/v1/cases/stats*', { forceNetworkError: true }).as('brokenStats');
    cy.intercept('GET', '**/api/v1/cases?*').as('cases');

    expectUncaughtException();
    cy.visitLocale('/', 'en');
    cy.wait('@cases');

    cy.get('[data-testid="case-card"]').should('have.length', 25);
    // The stat row is simply absent rather than rendering NaN or "undefined".
    cy.get('body').should('not.contain', 'NaN');
    cy.get('body').should('not.contain', 'undefined');
  });
});
