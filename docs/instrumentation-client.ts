import posthog from 'posthog-js';

const token = process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN;

if (process.env.NODE_ENV === 'production' && token) {
  posthog.init(token, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST ?? 'https://t.nustack.dev',
    ui_host: 'https://us.posthog.com',
    defaults: '2026-05-30',
  });
}
