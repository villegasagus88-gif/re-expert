// Sentry browser SDK — loaded lazily and only when SENTRY_DSN is set.
// Disabled in dev (localhost) so we don't pollute the Sentry quota with
// dev-only errors. Reads config from window.RE_CONFIG (config.js).
(function () {
  var cfg = (typeof window !== 'undefined' && window.RE_CONFIG) || {};
  if (!cfg.SENTRY_DSN) return;

  var host = (typeof window !== 'undefined' && window.location && window.location.hostname) || '';
  if (host === 'localhost' || host === '127.0.0.1') return;

  // CDN bundle — pinned version. Browser SDK is ~25 KB gzipped.
  var s = document.createElement('script');
  s.src = 'https://browser.sentry-cdn.com/7.119.0/bundle.tracing.min.js';
  s.crossOrigin = 'anonymous';
  s.onload = function () {
    if (!window.Sentry) return;
    window.Sentry.init({
      dsn: cfg.SENTRY_DSN,
      environment: cfg.SENTRY_ENVIRONMENT || 'production',
      release: cfg.VERSION || undefined,
      // Errors only by default. Bump tracesSampleRate in config.js if you
      // want performance data (counts against the 10k/month free tier).
      tracesSampleRate: typeof cfg.SENTRY_TRACES_SAMPLE_RATE === 'number'
        ? cfg.SENTRY_TRACES_SAMPLE_RATE
        : 0.0,
      // Don't ship request bodies / form data — they can contain user prompts / PII.
      sendDefaultPii: false,
      // Common noise to drop before it counts against quota.
      ignoreErrors: [
        'ResizeObserver loop limit exceeded',
        'ResizeObserver loop completed with undelivered notifications',
        'Non-Error promise rejection captured',
      ],
    });
  };
  s.onerror = function () {
    // CDN unreachable — fail silent, app must keep working without monitoring.
  };
  document.head.appendChild(s);
})();
