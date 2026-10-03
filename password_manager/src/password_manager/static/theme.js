/* Apply the theme before the stylesheet loads to prevent a color flash. */
(() => {
  'use strict';
  const key = 'keyvault-theme';
  const root = document.documentElement;
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  const isTheme = value => value === 'day' || value === 'night';
  let preference = null;
  try {
    const saved = localStorage.getItem(key);
    if (isTheme(saved)) preference = saved;
  } catch (_) { /* The selector also works when storage is unavailable. */ }

  function apply(theme) {
    root.dataset.theme = theme;
    root.style.colorScheme = theme === 'night' ? 'dark' : 'light';
    const night = theme === 'night';
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.querySelector('[data-theme-icon]').textContent = night ? '☀' : '☾';
      button.querySelector('[data-theme-label]').textContent = night ? 'Day mode' : 'Night mode';
      button.setAttribute('aria-label', night ? 'Switch to day mode' : 'Switch to night mode');
      button.title = night ? 'Switch to day mode' : 'Switch to night mode';
    });
  }

  const preferred = () => preference || (system.matches ? 'night' : 'day');
  apply(preferred());
  document.addEventListener('DOMContentLoaded', () => {
    apply(preferred());
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.addEventListener('click', () => {
        preference = root.dataset.theme === 'night' ? 'day' : 'night';
        try { localStorage.setItem(key, preference); } catch (_) { /* In-memory fallback. */ }
        apply(preference);
      });
    });
  });
  system.addEventListener('change', () => {
    if (!preference) apply(preferred());
  });
  window.addEventListener('storage', event => {
    if (event.key !== key && event.key !== null) return;
    preference = isTheme(event.newValue) ? event.newValue : null;
    apply(preferred());
  });
})();
