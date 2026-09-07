(() => {
  const root = document.querySelector('[data-onboarding]');
  if (!root) return;

  const panels = Array.from(document.querySelectorAll('[data-onboarding-step]'));
  const navButtons = Array.from(document.querySelectorAll('[data-step-nav]'));
  const total = panels.length;
  const storageKey = 'wisp-onboarding-clean-slate-v1';
  const toast = document.querySelector('[data-toast]');
  const progress = document.querySelector('[data-mobile-progress]');
  const mobileStep = document.querySelector('[data-mobile-step]');
  const mobileLabel = document.querySelector('[data-mobile-label]');
  const position = document.querySelector('[data-position]');
  const backButton = document.querySelector('[data-back]');
  const nextButton = document.querySelector('[data-next]');
  const restartButtons = Array.from(document.querySelectorAll('[data-restart]'));
  const localeLinks = Array.from(document.querySelectorAll('[data-locale-link]'));

  let state = {
    current: 0,
    visited: 0,
    choices: {},
    checks: {},
  };

  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
    state = {
      current: Number.isInteger(saved.current) ? saved.current : 0,
      visited: Number.isInteger(saved.visited) ? saved.visited : 0,
      choices: saved.choices && typeof saved.choices === 'object' ? saved.choices : {},
      checks: saved.checks && typeof saved.checks === 'object' ? saved.checks : {},
    };
  } catch (_) {}

  function persist() {
    try {
      localStorage.setItem(storageKey, JSON.stringify(state));
    } catch (_) {}
  }

  function indexFromHash() {
    const slug = window.location.hash.replace(/^#/, '');
    if (!slug) return null;
    const index = panels.findIndex((panel) => panel.dataset.onboardingStep === slug);
    return index >= 0 ? index : null;
  }

  function stepComplete(index) {
    const panel = panels[index];
    if (!panel) return false;
    const choiceKey = panel.dataset.requireChoice;
    const checkKey = panel.dataset.requireCheck;
    const choiceOk = !choiceKey || Boolean(state.choices[choiceKey]);
    const checkOk = !checkKey || Boolean(state.checks[checkKey]);
    return choiceOk && checkOk;
  }

  function syncControls() {
    document.querySelectorAll('[data-choice-key]').forEach((button) => {
      const selected = state.choices[button.dataset.choiceKey] === button.dataset.choiceValue;
      button.setAttribute('aria-pressed', String(selected));
    });

    document.querySelectorAll('[data-check-key]').forEach((input) => {
      input.checked = Boolean(state.checks[input.dataset.checkKey]);
    });
  }

  function syncLocaleLinks() {
    localeLinks.forEach((link) => {
      const base = link.dataset.localeBase || link.getAttribute('href') || '/';
      const mapped = (link.dataset.localeSteps || '').split(',')[state.current];
      const slug = mapped || panels[state.current]?.dataset.onboardingStep || '';
      link.href = `${base}${slug ? `#${slug}` : ''}`;
    });
  }

  function render(direction = 'forward', updateHash = true) {
    state.current = Math.max(0, Math.min(total - 1, state.current));
    state.visited = Math.max(state.visited, state.current);
    persist();
    syncControls();

    panels.forEach((panel, index) => {
      const active = index === state.current;
      panel.hidden = !active;
      if (active) panel.dataset.direction = direction;
    });

    navButtons.forEach((button, index) => {
      const current = index === state.current;
      const visited = index <= state.visited;
      button.toggleAttribute('aria-current', current);
      if (current) button.setAttribute('aria-current', 'step');
      button.dataset.visited = String(visited);
      button.dataset.complete = String(index < state.current || stepComplete(index));
      button.disabled = !visited;
      const status = button.querySelector('[data-step-state]');
      if (status) {
        status.textContent = current ? (status.dataset.current || '') : index < state.current ? (status.dataset.done || '') : '';
      }
    });

    const activePanel = panels[state.current];
    const stepLabel = activePanel?.dataset.stepLabel || '';
    if (position) position.textContent = `${state.current + 1} / ${total} · ${stepLabel}`;
    if (mobileStep) mobileStep.textContent = `${state.current + 1} / ${total}`;
    if (mobileLabel) mobileLabel.textContent = stepLabel;
    if (progress) progress.style.width = `${((state.current + 1) / total) * 100}%`;

    if (backButton) backButton.disabled = state.current === 0;
    if (nextButton) {
      nextButton.hidden = state.current === total - 1;
      nextButton.disabled = !stepComplete(state.current);
      const customLabel = activePanel?.dataset.nextLabel;
      nextButton.textContent = customLabel || nextButton.dataset.defaultLabel || 'Continuer';
    }

    syncLocaleLinks();
    if (updateHash) {
      const slug = activePanel?.dataset.onboardingStep;
      if (slug) history.replaceState(null, '', `${window.location.pathname}${window.location.search}#${slug}`);
    }

    const stage = document.querySelector('[data-stage-main]');
    if (stage) stage.scrollTo({ top: 0, behavior: 'auto' });
  }

  function focusActiveHeading() {
    const heading = panels[state.current]?.querySelector('h1,h2');
    if (!heading) return;
    heading.setAttribute('tabindex', '-1');
    heading.focus({ preventScroll: true });
  }

  function goTo(index, direction = 'forward') {
    if (index < 0 || index >= total) return;
    state.current = index;
    render(direction);
    requestAnimationFrame(focusActiveHeading);
  }

  function refreshRequirement() {
    if (nextButton) nextButton.disabled = !stepComplete(state.current);
    navButtons.forEach((button, index) => {
      button.dataset.complete = String(index < state.current || stepComplete(index));
    });
    persist();
  }

  document.addEventListener('click', (event) => {
    const choice = event.target.closest('[data-choice-key]');
    if (choice) {
      state.choices[choice.dataset.choiceKey] = choice.dataset.choiceValue;
      syncControls();
      refreshRequirement();
      return;
    }

    const nav = event.target.closest('[data-step-nav]');
    if (nav && !nav.disabled) {
      const index = Number(nav.dataset.stepNav);
      goTo(index, index < state.current ? 'back' : 'forward');
      return;
    }

    const copy = event.target.closest('[data-copy-id]');
    if (copy) {
      const source = document.getElementById(copy.dataset.copyId);
      const text = source?.value ?? source?.textContent ?? '';
      copyText(text).then(() => showToast(copy.dataset.copied || 'Copié'));
      return;
    }

    const direct = event.target.closest('[data-go-step]');
    if (direct) {
      const index = panels.findIndex((panel) => panel.dataset.onboardingStep === direct.dataset.goStep);
      if (index >= 0) goTo(index, index < state.current ? 'back' : 'forward');
    }
  });

  document.querySelectorAll('[data-check-key]').forEach((input) => {
    input.addEventListener('change', () => {
      state.checks[input.dataset.checkKey] = input.checked;
      refreshRequirement();
    });
  });

  if (backButton) backButton.addEventListener('click', () => goTo(state.current - 1, 'back'));
  if (nextButton) nextButton.addEventListener('click', () => {
    if (!stepComplete(state.current)) return;
    goTo(state.current + 1, 'forward');
  });

  restartButtons.forEach((button) => {
    button.addEventListener('click', () => {
      try { localStorage.removeItem(storageKey); } catch (_) {}
      state = { current: 0, visited: 0, choices: {}, checks: {} };
      goTo(0, 'back');
    });
  });

  window.addEventListener('hashchange', () => {
    const index = indexFromHash();
    if (index !== null && index <= state.visited) {
      const previous = state.current;
      state.current = index;
      render(index < previous ? 'back' : 'forward', false);
    }
  });

  function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.hidden = false;
    clearTimeout(showToast.timer);
    showToast.timer = setTimeout(() => { toast.hidden = true; }, 1500);
  }

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    document.execCommand('copy');
    area.remove();
  }

  const hashed = indexFromHash();
  if (hashed !== null) {
    state.current = hashed;
    state.visited = Math.max(state.visited, hashed);
  } else {
    state.current = Math.min(state.current, total - 1);
  }
  render('forward');
})();
