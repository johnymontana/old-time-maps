import { inject } from '@vercel/analytics';
import { injectSpeedInsights } from '@vercel/speed-insights';

// Production HTML can also be downloaded and opened locally.
const hostname = window.location.hostname;
const local = hostname === 'localhost' || hostname.endsWith('.localhost') ||
  hostname === '[::1]' || hostname === '0.0.0.0' || hostname.startsWith('127.');

if (window.location.protocol === 'https:' && !local) {
  // The Python assembler forwards Vercel's deployment-specific public routes.
  const config = document.currentScript.dataset.config;
  inject({ mode: 'production' }, config);
  injectSpeedInsights({}, config);
}
