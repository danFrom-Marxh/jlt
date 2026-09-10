'use strict';

function getCookie(name) {
  let value = null;
  if (document.cookie) {
    document.cookie.split(';').forEach((cookie) => {
      const item = cookie.trim();
      if (item.startsWith(`${name}=`)) value = decodeURIComponent(item.slice(name.length + 1));
    });
  }
  return value;
}

function showLoading() {
  const spinner = document.getElementById('loading-spinner');
  spinner?.classList.remove('hidden');
  spinner?.setAttribute('aria-hidden', 'false');
}

function hideLoading() {
  const spinner = document.getElementById('loading-spinner');
  spinner?.classList.add('hidden');
  spinner?.setAttribute('aria-hidden', 'true');
}

function showToast(message, type = 'info') {
  const stack = document.getElementById('toast-stack');
  if (!stack) return;
  const element = document.createElement('div');
  element.className = `toast ${type}`;
  element.textContent = message;
  stack.appendChild(element);
  window.setTimeout(() => {
    element.style.opacity = '0';
    element.style.transform = 'translateY(-6px)';
    window.setTimeout(() => element.remove(), 220);
  }, 3400);
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;',
  }[char]));
}

window.getCookie = getCookie;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showToast = showToast;

// Centralized scroll lock. Multiple overlays can coexist without accidentally
// unlocking the page when only one of them is closed.
(function setupPageLock() {
  const locks = new Set();
  let scrollY = 0;

  function applyLock() {
    if (locks.size !== 1) return;
    scrollY = window.scrollY || document.documentElement.scrollTop || 0;
    document.body.style.top = `-${scrollY}px`;
    document.body.classList.add('no-scroll');
  }

  function removeLock() {
    if (locks.size !== 0) return;
    document.body.classList.remove('no-scroll');
    document.body.style.top = '';
    window.scrollTo(0, scrollY);
  }

  window.JLTPageLock = {
    acquire(key) {
      if (!key || locks.has(key)) return;
      locks.add(key);
      applyLock();
    },
    release(key) {
      if (!key || !locks.has(key)) return;
      locks.delete(key);
      removeLock();
    },
    isLocked() {
      return locks.size > 0;
    },
  };
})();

const overlay = document.getElementById('pageOverlay');
const drawer = document.getElementById('cartDrawer');
const mobile = document.getElementById('mobileNav');
const searchPanel = document.getElementById('searchPanel');
const searchInput = document.getElementById('globalSearchInput');
let searchTimer;

function syncPageOverlay() {
  const active = Boolean(drawer?.classList.contains('open') || mobile?.classList.contains('open'));
  overlay?.classList.toggle('active', active);
}

function closePanels() {
  drawer?.classList.remove('open');
  mobile?.classList.remove('open');
  drawer?.setAttribute('aria-hidden', 'true');
  mobile?.setAttribute('aria-hidden', 'true');
  syncPageOverlay();
  window.JLTPageLock?.release('side-panel');
}

async function loadCartDrawer() {
  const box = document.getElementById('drawerItems');
  if (!box) return;
  box.innerHTML = '<div class="drawer-loading">Chargement du panier…</div>';
  try {
    const response = await fetch(window.JLT.cartSummaryUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    const data = await response.json();
    document.getElementById('badge').textContent = data.count;
    document.getElementById('drawerCount').textContent = `(${data.count})`;
    document.getElementById('drawerTotal').textContent = `${Number(data.total).toFixed(2)} ${window.JLT.currencySymbol}`;
    if (!data.items.length) {
      box.innerHTML = '<div class="drawer-empty"><i class="bi bi-bag"></i><strong>Votre panier est vide</strong><p>Ajoutez un produit pour commencer.</p></div>';
      return;
    }
    box.innerHTML = data.items.map((item) => `<a class="drawer-item" href="/produit/${item.slug}/"><img src="${item.image || '/static/images/No-image.jpg'}" onerror="this.onerror=null;this.src='/static/images/No-image.jpg'" alt=""><div class="drawer-item-meta"><div><h4>${escapeHtml(item.name)}</h4><p>${escapeHtml(item.variant || '')}</p></div><span class="drawer-item-qty">Qté ${item.quantity}</span></div><strong>${Number(item.subtotal).toFixed(2)} ${window.JLT.currencySymbol}</strong></a>`).join('');
  } catch (_error) {
    box.innerHTML = '<div class="drawer-empty">Impossible de charger le panier.</div>';
  }
}

function closeSearch() {
  searchPanel?.classList.remove('open');
  searchPanel?.setAttribute('aria-hidden', 'true');
  window.JLTPageLock?.release('search');
}

function openCart() {
  closeSearch();
  mobile?.classList.remove('open');
  mobile?.setAttribute('aria-hidden', 'true');
  drawer?.classList.add('open');
  drawer?.setAttribute('aria-hidden', 'false');
  window.JLTPageLock?.acquire('side-panel');
  syncPageOverlay();
  loadCartDrawer();
}
window.openCart = openCart;

function openMobileMenu() {
  closeSearch();
  drawer?.classList.remove('open');
  drawer?.setAttribute('aria-hidden', 'true');
  mobile?.classList.add('open');
  mobile?.setAttribute('aria-hidden', 'false');
  window.JLTPageLock?.acquire('side-panel');
  syncPageOverlay();
  mobile?.scrollTo({ top: 0, behavior: 'auto' });
  document.getElementById('mobileNavClose')?.focus({ preventScroll: true });
}

function openSearch() {
  closePanels();
  searchPanel?.classList.add('open');
  searchPanel?.setAttribute('aria-hidden', 'false');
  window.JLTPageLock?.acquire('search');
  window.setTimeout(() => searchInput?.focus({ preventScroll: true }), 80);
}

document.getElementById('cartToggle')?.addEventListener('click', openCart);
document.getElementById('cartClose')?.addEventListener('click', closePanels);
document.getElementById('menuToggle')?.addEventListener('click', openMobileMenu);
document.getElementById('mobileNavClose')?.addEventListener('click', closePanels);
overlay?.addEventListener('click', closePanels);
document.getElementById('searchToggle')?.addEventListener('click', openSearch);
document.getElementById('searchClose')?.addEventListener('click', closeSearch);
searchPanel?.addEventListener('click', (event) => {
  if (event.target === searchPanel) closeSearch();
});

document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  if (searchPanel?.classList.contains('open')) closeSearch();
  else closePanels();
});

searchInput?.addEventListener('input', () => {
  clearTimeout(searchTimer);
  const query = searchInput.value.trim();
  const results = document.getElementById('autocompleteResults');
  if (!results) return;
  if (query.length < 2) {
    results.innerHTML = '';
    return;
  }
  searchTimer = window.setTimeout(async () => {
    try {
      const response = await fetch(`${window.JLT.searchApi}?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      results.innerHTML = (data.results || []).map((product) => `<a class="autocomplete-item" href="/produit/${product.slug}/"><img src="${product.image || '/static/images/No-image.jpg'}" onerror="this.onerror=null;this.src='/static/images/No-image.jpg'" alt=""><strong>${escapeHtml(product.name)}</strong><span>${Number(product.price).toFixed(2)} ${window.JLT.currencySymbol}</span></a>`).join('');
    } catch (_error) {
      results.innerHTML = '';
    }
  }, 220);
});

async function addToCart(slug, quantity = 1, variant = null) {
  showLoading();
  try {
    const response = await fetch(`/panier/ajouter/${slug}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ quantity, variant_id: variant, variante: variant }),
    });
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.message || 'Impossible d’ajouter ce produit.');
    document.getElementById('badge').textContent = data.panier;
    showToast(data.message, 'success');
    openCart();
    return data;
  } catch (error) {
    showToast(error.message || 'Une erreur est survenue.', 'error');
    return null;
  } finally {
    hideLoading();
  }
}
window.addToCart = addToCart;

document.addEventListener('click', (event) => {
  const button = event.target.closest('.js-add-cart');
  if (!button) return;
  event.preventDefault();
  addToCart(button.dataset.slug, parseInt(button.dataset.quantity || '1', 10), button.dataset.variant || null);
});

async function startStripeCheckout(payload) {
  showLoading();
  try {
    const response = await fetch(window.JLT.checkoutUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.message || 'Le paiement ne peut pas démarrer.');
    window.location.href = data.url;
  } catch (error) {
    showToast(error.message || 'Erreur de paiement.', 'error');
    hideLoading();
  }
}
window.startStripeCheckout = startStripeCheckout;

document.addEventListener('click', (event) => {
  const button = event.target.closest('.js-stripe-checkout');
  if (!button) return;
  event.preventDefault();
  startStripeCheckout({ source: button.dataset.source || 'cart' });
});

document.addEventListener('click', async (event) => {
  const button = event.target.closest('.js-cart-update');
  if (!button) return;
  event.preventDefault();
  showLoading();
  try {
    const response = await fetch('/api/update_cart/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ item_id: button.dataset.id, action: button.dataset.action }),
    });
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.message || 'Impossible de modifier le panier.');
    location.reload();
  } catch (error) {
    showToast(error.message, 'error');
    hideLoading();
  }
});

window.setTimeout(() => {
  document.querySelectorAll('.flash').forEach((element) => {
    element.style.transition = 'opacity .25s';
    element.style.opacity = '0';
    window.setTimeout(() => element.remove(), 300);
  });
}, 3200);

const scrollTopButton = document.getElementById('scrollTopButton');
function syncScrollTopButton() {
  scrollTopButton?.classList.toggle('visible', window.scrollY > 520);
}
window.addEventListener('scroll', syncScrollTopButton, { passive: true });
syncScrollTopButton();
scrollTopButton?.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

// Cookie choice first, newsletter second.
const cookieModal = document.getElementById('cookieModal');
const newsletterModal = document.getElementById('newsletterModal');

function modalLockKey(modal) {
  return `site-modal:${modal?.id || 'unknown'}`;
}

function openSiteModal(modal) {
  if (!modal) return;
  closeSearch();
  closePanels();
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
  window.JLTPageLock?.acquire(modalLockKey(modal));
  const firstButton = modal.querySelector('button,input,select,textarea,a[href]');
  window.setTimeout(() => firstButton?.focus({ preventScroll: true }), 60);
}

function closeSiteModal(modal) {
  if (!modal) return;
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
  window.JLTPageLock?.release(modalLockKey(modal));
}

function setConsentCookie(value) {
  try { localStorage.setItem('jlt_cookie_consent', value); } catch (_error) {}
  const secure = location.protocol === 'https:' ? '; Secure' : '';
  document.cookie = `jlt_cookie_consent=${encodeURIComponent(value)}; Max-Age=31536000; Path=/; SameSite=Lax${secure}`;
}

function getConsentChoice() {
  try { return localStorage.getItem('jlt_cookie_consent') || getCookie('jlt_cookie_consent'); }
  catch (_error) { return getCookie('jlt_cookie_consent'); }
}

function newsletterAlreadyHandled() {
  try { return localStorage.getItem('jlt_newsletter_handled') === '1'; }
  catch (_error) { return false; }
}

function maybeOpenNewsletter() {
  if (newsletterAlreadyHandled()) return;
  window.setTimeout(() => openSiteModal(newsletterModal), 650);
}

document.querySelectorAll('[data-cookie-choice]').forEach((button) => button.addEventListener('click', () => {
  setConsentCookie(button.dataset.cookieChoice);
  closeSiteModal(cookieModal);
  maybeOpenNewsletter();
}));

document.getElementById('openCookiePreferences')?.addEventListener('click', () => openSiteModal(cookieModal));
document.querySelectorAll('[data-newsletter-close]').forEach((button) => button.addEventListener('click', () => {
  try { localStorage.setItem('jlt_newsletter_handled', '1'); } catch (_error) {}
  closeSiteModal(newsletterModal);
}));

async function subscribeNewsletter(form) {
  const email = form.querySelector('[name="email"]')?.value?.trim();
  if (!email) return;
  const submit = form.querySelector('[type="submit"]');
  if (submit) {
    submit.disabled = true;
    submit.dataset.originalText = submit.innerHTML;
    submit.textContent = 'Inscription…';
  }
  try {
    const response = await fetch(window.JLT.newsletterUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ email }),
    });
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.message || 'Inscription impossible.');
    try {
      localStorage.setItem('jlt_newsletter_handled', '1');
      localStorage.setItem('jlt_newsletter_subscribed', '1');
    } catch (_error) {}
    form.outerHTML = `<div class="newsletter-success"><strong>${escapeHtml(data.message)}</strong><span>Utilisez ce code dans votre panier :</span><div class="newsletter-code-row"><span class="newsletter-code">${escapeHtml(data.promo_code)}</span><button type="button" class="newsletter-code-copy" data-copy-code="${escapeHtml(data.promo_code)}">Copier</button></div></div>`;
    showToast(`Votre code -8 % : ${data.promo_code}`, 'success');
  } catch (error) {
    showToast(error.message || 'Inscription impossible.', 'error');
    if (submit) {
      submit.disabled = false;
      submit.innerHTML = submit.dataset.originalText || 'Réessayer';
    }
  }
}

document.addEventListener('submit', (event) => {
  const form = event.target.closest('.js-newsletter-form');
  if (!form) return;
  event.preventDefault();
  subscribeNewsletter(form);
});

document.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-copy-code]');
  if (!button) return;
  try {
    await navigator.clipboard.writeText(button.dataset.copyCode);
    button.textContent = 'Copié';
    showToast('Code copié.', 'success');
  } catch (_error) {
    showToast(`Code : ${button.dataset.copyCode}`, 'info');
  }
});

window.addEventListener('DOMContentLoaded', () => {
  if (!getConsentChoice()) window.setTimeout(() => openSiteModal(cookieModal), 450);
  else maybeOpenNewsletter();
});
