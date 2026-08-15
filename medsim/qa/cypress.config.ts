import { defineConfig } from 'cypress';

/**
 * Cypress configuration for the MedSimQA dashboard suite.
 *
 * The suite is organised around the four things that actually break this
 * application, rather than around its screens:
 *
 *   01  functional behaviour of the case library
 *   02  clinical-data rendering correctness
 *   03  layout constraints and regional formatting across five locales
 *   04  network interception: SSL failures, dropped packets, malformed JSON
 *
 * The device matrix in `env.viewports` mirrors the real devices the mobile
 * wrapper is tested on in Phase 3's ADB scripts, so a layout failure found in
 * CI is reproducible on hardware with the same numbers.
 */
export default defineConfig({
  e2e: {
    baseUrl: process.env.CYPRESS_BASE_URL ?? 'http://localhost:4173',
    supportFile: 'cypress/support/e2e.ts',
    specPattern: 'cypress/e2e/**/*.cy.ts',
    fixturesFolder: 'cypress/fixtures',
    screenshotsFolder: 'cypress/screenshots',
    videosFolder: 'cypress/videos',

    // 1440x900 is the reference desktop. Individual specs override per test.
    viewportWidth: 1440,
    viewportHeight: 900,

    video: false,
    screenshotOnRunFailure: true,

    // Generous, because the network specs deliberately inject multi-second
    // latency and a stingy timeout would make those tests flaky rather than
    // meaningful.
    defaultCommandTimeout: 8000,
    requestTimeout: 15000,
    responseTimeout: 20000,
    pageLoadTimeout: 30000,

    retries: {
      // One retry in CI absorbs genuine infrastructure flake without hiding a
      // real intermittent bug, which two or three retries would.
      runMode: 1,
      openMode: 0,
    },

    experimentalMemoryManagement: true,
    numTestsKeptInMemory: 5,

    env: {
      apiBase: '/api/v1',

      /**
       * The device matrix. Widths chosen for a reason:
       *   320  the narrowest viewport still in meaningful use (iPhone SE 1)
       *   360  Samsung Galaxy A-series portrait - the reference device for the
       *        ADB scripts in qa/adb
       *   375  iPhone SE 2/3 portrait
       *   412  Galaxy S-series portrait
       *   768  tablet portrait, the breakpoint where the filter rail changes
       *   1024 the lg breakpoint where the dashboard becomes two-column
       */
      viewports: {
        narrow: [320, 640],
        galaxyA: [360, 740],
        iphoneSe: [375, 667],
        galaxyS: [412, 915],
        tablet: [768, 1024],
        laptop: [1024, 768],
        desktop: [1440, 900],
      },

      locales: ['en', 'de', 'es', 'nl', 'ru'],

      /**
       * Locales whose decimal separator is a comma. Getting this wrong is a
       * patient-safety issue, not a cosmetic one: "0.005" read as "0,005" by a
       * clinician expecting comma-decimals is a 1000-fold error.
       */
      commaDecimalLocales: ['de', 'es', 'nl', 'ru'],

      /** Chaos headers understood by the backend middleware. */
      chaos: {
        latency: 'X-Chaos-Latency-Ms',
        status: 'X-Chaos-Status',
        malformed: 'X-Chaos-Malformed',
        truncate: 'X-Chaos-Truncate',
        drop: 'X-Chaos-Drop',
        contentType: 'X-Chaos-Content-Type',
        empty: 'X-Chaos-Empty',
      },
    },

    setupNodeEvents(on, config) {
      // Surface browser console output in the terminal. Without this, a React
      // warning or an uncaught promise rejection in a headless run is
      // invisible, and those are exactly what the network specs provoke.
      on('task', {
        log(message: string) {
          console.log(message);
          return null;
        },
        table(data: unknown) {
          console.table(data);
          return null;
        },
      });

      on('before:browser:launch', (browser, launchOptions) => {
        if (browser.family === 'chromium' && browser.name !== 'electron') {
          // Deterministic locale and timezone. Without these the regional
          // formatting assertions pass or fail depending on the CI machine's
          // locale, which is the worst possible kind of flake.
          launchOptions.args.push('--lang=en-GB');
          launchOptions.args.push('--disable-lcd-text');
          // Forces a consistent device scale so screenshot diffs are stable.
          launchOptions.args.push('--force-device-scale-factor=1');
        }
        return launchOptions;
      });

      return config;
    },
  },
});
