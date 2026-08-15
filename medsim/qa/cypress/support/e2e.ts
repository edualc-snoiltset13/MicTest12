/// <reference types="cypress" />

import './commands';

/**
 * Global test setup.
 *
 * The uncaught-exception policy is the important part. By default Cypress
 * fails a test on any unhandled browser exception, which would make the
 * network-interception specs unusable: provoking a malformed response is the
 * point of those tests, and the application is *supposed* to survive it. So
 * the policy is inverted deliberately - an exception the application handles
 * is not a failure; an exception that reaches the window IS, unless the test
 * has explicitly declared that it expects one.
 */

let expectingUncaught = false;

/** Called by a spec that deliberately provokes an unhandled rejection. */
export function expectUncaughtException(): void {
  expectingUncaught = true;
}

Cypress.on('uncaught:exception', (error) => {
  if (expectingUncaught) {
    expectingUncaught = false;
    return false; // swallow
  }

  // ResizeObserver's benign loop notification is a browser quirk, not a bug.
  // Chrome fires it whenever an observed element is resized during layout,
  // which the responsive chart does on every viewport change.
  if (/ResizeObserver loop/.test(error.message)) {
    return false;
  }

  // Everything else fails the test, with the message intact.
  return true;
});

beforeEach(() => {
  expectingUncaught = false;

  // A clean slate per test. Locale and theme both persist to localStorage, and
  // a test that inherits the previous test's language is a false pass.
  cy.clearLocalStorage();
  cy.window({ log: false }).then((win) => {
    win.sessionStorage.clear();
  });
});

// Console errors are collected per test and asserted on demand by specs that
// care. Collecting them always, rather than failing on them always, keeps the
// deliberate-failure specs readable.
declare global {
  interface Window {
    __consoleErrors?: string[];
  }
}

Cypress.on('window:before:load', (win) => {
  win.__consoleErrors = [];
  const original = win.console.error;
  win.console.error = (...args: unknown[]) => {
    win.__consoleErrors!.push(args.map(String).join(' '));
    original.apply(win.console, args as []);
  };
});
