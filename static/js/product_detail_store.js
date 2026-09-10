(function () {
  'use strict';

  function initProductDetail() {
    const root = document.getElementById('productDetailRoot');
    if (!root || root.dataset.jltInitialized === '1') return;
    root.dataset.jltInitialized = '1';
    document.body.classList.add('product-detail-active');

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function createSwipeSlider({ viewport, track, slides, onIndexChange }) {
      if (!viewport || !track || !slides.length) return null;

      let index = 0;
      let width = 1;
      let pointerId = null;
      let startX = 0;
      let startY = 0;
      let lastX = 0;
      let lastTime = 0;
      let velocityX = 0;
      let deltaX = 0;
      let horizontal = false;
      let dragging = false;
      let raf = 0;
      let pendingX = 0;
      let suppressClickUntil = 0;

      const measure = () => {
        width = Math.max(1, viewport.clientWidth || 1);
        return width;
      };

      const applyTransform = (x, animate = true) => {
        if (raf) cancelAnimationFrame(raf);
        raf = 0;
        track.style.transition = animate && !prefersReducedMotion
          ? 'transform 340ms cubic-bezier(.22,1,.36,1)'
          : 'none';
        track.style.transform = `translate3d(${x}px,0,0)`;
      };

      const queueTransform = (x) => {
        pendingX = x;
        if (raf) return;
        raf = requestAnimationFrame(() => {
          raf = 0;
          track.style.transform = `translate3d(${pendingX}px,0,0)`;
        });
      };

      const goTo = (nextIndex, animate = true) => {
        index = Math.max(0, Math.min(slides.length - 1, nextIndex));
        applyTransform(-index * measure(), animate);
        onIndexChange?.(index);
      };

      const resetPointer = () => {
        if (pointerId !== null) {
          try {
            if (viewport.hasPointerCapture?.(pointerId)) viewport.releasePointerCapture(pointerId);
          } catch (_error) {}
        }
        pointerId = null;
        dragging = false;
        horizontal = false;
        deltaX = 0;
        velocityX = 0;
        viewport.classList.remove('is-dragging');
      };

      viewport.addEventListener('pointerdown', (event) => {
        if (slides.length < 2) return;
        if (event.target.closest('button,a,input,select,textarea')) return;
        if (event.pointerType === 'mouse' && event.button !== 0) return;
        pointerId = event.pointerId;
        dragging = true;
        horizontal = false;
        startX = lastX = event.clientX;
        startY = event.clientY;
        lastTime = performance.now();
        velocityX = 0;
        deltaX = 0;
        measure();
      }, { passive: true });

      viewport.addEventListener('pointermove', (event) => {
        if (!dragging || event.pointerId !== pointerId) return;
        const dx = event.clientX - startX;
        const dy = event.clientY - startY;

        if (!horizontal) {
          const ax = Math.abs(dx);
          const ay = Math.abs(dy);
          if (ax < 6 && ay < 6) return;
          if (ay > ax * 1.05) {
            resetPointer();
            return;
          }
          horizontal = true;
          try { viewport.setPointerCapture?.(pointerId); } catch (_error) {}
          viewport.classList.add('is-dragging');
          track.style.transition = 'none';
        }

        event.preventDefault();
        const now = performance.now();
        const dt = Math.max(1, now - lastTime);
        const instantVelocity = (event.clientX - lastX) / dt;
        velocityX = velocityX * 0.72 + instantVelocity * 0.28;
        lastX = event.clientX;
        lastTime = now;
        deltaX = dx;

        let visualDelta = dx;
        if ((index === 0 && dx > 0) || (index === slides.length - 1 && dx < 0)) {
          visualDelta *= 0.24;
        }
        queueTransform((-index * width) + visualDelta);
      }, { passive: false });

      const finish = (event) => {
        if (!dragging || event.pointerId !== pointerId) return;
        const movedHorizontally = horizontal;
        const finalDelta = deltaX;
        const finalVelocity = velocityX;
        resetPointer();

        if (!movedHorizontally) {
          applyTransform(-index * measure(), true);
          return;
        }

        suppressClickUntil = performance.now() + 320;
        const distanceThreshold = Math.min(width * 0.16, 90);
        const velocityThreshold = 0.38;
        let target = index;
        if (finalDelta < -distanceThreshold || finalVelocity < -velocityThreshold) target += 1;
        if (finalDelta > distanceThreshold || finalVelocity > velocityThreshold) target -= 1;
        goTo(target, true);
      };

      viewport.addEventListener('pointerup', finish, { passive: true });
      viewport.addEventListener('pointercancel', finish, { passive: true });
      viewport.addEventListener('dragstart', (event) => event.preventDefault());

      const realign = () => applyTransform(-index * measure(), false);
      if ('ResizeObserver' in window) {
        const observer = new ResizeObserver(() => requestAnimationFrame(realign));
        observer.observe(viewport);
      } else {
        window.addEventListener('resize', () => requestAnimationFrame(realign), { passive: true });
      }

      goTo(0, false);
      return {
        goTo,
        next: () => goTo(index + 1),
        prev: () => goTo(index - 1),
        getIndex: () => index,
        clickSuppressed: () => performance.now() < suppressClickUntil,
        realign,
      };
    }

    // --- Main product gallery. ---
    const galleryViewport = document.getElementById('galleryMain');
    const galleryTrack = document.getElementById('galleryTrack');
    const gallerySlides = galleryTrack ? [...galleryTrack.querySelectorAll('.gallery-slide')] : [];
    const galleryThumbsStrip = document.getElementById('galleryThumbs');
    const galleryThumbs = [...document.querySelectorAll('.gallery-thumb')];
    const galleryCurrent = document.getElementById('galleryCurrent');
    const galleryPrev = document.querySelector('.gallery-prev');
    const galleryNext = document.querySelector('.gallery-next');

    function centerActiveThumb(index) {
      const thumb = galleryThumbs[index];
      if (!galleryThumbsStrip || !thumb) return;
      const stripRect = galleryThumbsStrip.getBoundingClientRect();
      const thumbRect = thumb.getBoundingClientRect();
      const target = galleryThumbsStrip.scrollLeft + thumbRect.left - stripRect.left - ((galleryThumbsStrip.clientWidth - thumbRect.width) / 2);
      galleryThumbsStrip.scrollTo({ left: Math.max(0, target), behavior: prefersReducedMotion ? 'auto' : 'smooth' });
    }

    const gallerySlider = createSwipeSlider({
      viewport: galleryViewport,
      track: galleryTrack,
      slides: gallerySlides,
      onIndexChange(index) {
        galleryThumbs.forEach((thumb, i) => thumb.classList.toggle('active', i === index));
        if (galleryCurrent) galleryCurrent.textContent = String(index + 1);
        if (galleryPrev) galleryPrev.disabled = index === 0;
        if (galleryNext) galleryNext.disabled = index === gallerySlides.length - 1;
        centerActiveThumb(index);
      },
    });

    galleryPrev?.addEventListener('click', () => gallerySlider?.prev());
    galleryNext?.addEventListener('click', () => gallerySlider?.next());
    galleryThumbs.forEach((thumb, index) => thumb.addEventListener('click', () => gallerySlider?.goTo(index)));

    function goToImageUrl(url) {
      if (!url || !gallerySlider) return;
      const index = gallerySlides.findIndex((slide) => slide.dataset.imageUrl === url);
      if (index >= 0) gallerySlider.goTo(index);
    }

    // --- Full-screen lightbox with its own touch slider. ---
    const lightbox = document.getElementById('productLightbox');
    const lightboxViewport = document.getElementById('productLightboxViewport');
    const lightboxTrack = document.getElementById('productLightboxTrack');
    const lightboxSlides = lightboxTrack ? [...lightboxTrack.querySelectorAll('.product-lightbox-slide')] : [];
    const lightboxClose = document.getElementById('productLightboxClose');
    const lightboxPrev = document.querySelector('.product-lightbox-prev');
    const lightboxNext = document.querySelector('.product-lightbox-next');
    const lightboxCurrent = document.getElementById('productLightboxCurrent');
    const galleryExpand = document.getElementById('galleryExpand');
    let lastLightboxFocus = null;

    const lightboxSlider = createSwipeSlider({
      viewport: lightboxViewport,
      track: lightboxTrack,
      slides: lightboxSlides,
      onIndexChange(index) {
        if (lightboxCurrent) lightboxCurrent.textContent = String(index + 1);
        if (lightboxPrev) lightboxPrev.disabled = index === 0;
        if (lightboxNext) lightboxNext.disabled = index === lightboxSlides.length - 1;
      },
    });

    function openLightbox(index = gallerySlider?.getIndex() || 0) {
      if (!lightbox || !lightboxSlider) return;
      lastLightboxFocus = document.activeElement;
      lightboxSlider.goTo(index, false);
      lightbox.classList.add('open');
      lightbox.setAttribute('aria-hidden', 'false');
      window.JLTPageLock?.acquire('product-lightbox');
      requestAnimationFrame(() => {
        lightboxSlider.realign();
        lightboxClose?.focus({ preventScroll: true });
      });
    }

    function closeLightbox() {
      if (!lightbox?.classList.contains('open')) return;
      lightbox.classList.remove('open');
      lightbox.setAttribute('aria-hidden', 'true');
      window.JLTPageLock?.release('product-lightbox');
      if (lastLightboxFocus instanceof HTMLElement) lastLightboxFocus.focus({ preventScroll: true });
    }

    galleryExpand?.addEventListener('click', () => openLightbox());
    galleryViewport?.addEventListener('click', (event) => {
      if (event.target.closest('.gallery-nav,.gallery-expand') || gallerySlider?.clickSuppressed()) return;
      openLightbox();
    });
    lightboxClose?.addEventListener('click', closeLightbox);
    lightbox?.querySelectorAll('[data-lightbox-close]').forEach((node) => node.addEventListener('click', closeLightbox));
    lightbox?.querySelector('.product-lightbox-dialog')?.addEventListener('click', (event) => {
      if (event.target.classList.contains('product-lightbox-dialog')) closeLightbox();
    });
    lightboxPrev?.addEventListener('click', () => lightboxSlider?.prev());
    lightboxNext?.addEventListener('click', () => lightboxSlider?.next());

    // --- Variant selection and guided recovery. ---
    const variantSection = document.getElementById('variantSection');
    const variantHelp = document.getElementById('variantHelp');
    const variantButtons = [...document.querySelectorAll('.variant-option:not(.disabled):not(:disabled)')];
    const quantityInput = document.getElementById('productQuantity');
    const detailAdd = document.getElementById('detailAddCart');
    const fixedAdd = document.getElementById('fixedAddCart');
    const buyNow = document.getElementById('buyNowButton');
    const fixedLabel = document.getElementById('fixedVariantLabel');
    const fixedBar = document.getElementById('productFixedCta');
    const primaryZone = document.getElementById('primaryPurchaseZone');
    let selectedVariant = null;
    let cartRequestBusy = false;

    function selectVariant(button) {
      if (!button) return;
      variantButtons.forEach((item) => item.classList.remove('selected'));
      button.classList.add('selected');
      button.setAttribute('aria-pressed', 'true');
      variantButtons.filter((item) => item !== button).forEach((item) => item.setAttribute('aria-pressed', 'false'));
      selectedVariant = button.dataset.variantId || null;
      if (variantHelp) variantHelp.textContent = 'Option sélectionnée';
      if (fixedLabel) fixedLabel.textContent = button.textContent.replace(/\s+/g, ' ').trim();
      variantSection?.classList.remove('needs-attention', 'is-highlighted');
      goToImageUrl(button.dataset.image);
    }

    if (variantButtons.length === 1) selectVariant(variantButtons[0]);
    variantButtons.forEach((button) => {
      button.setAttribute('aria-pressed', 'false');
      button.addEventListener('click', () => selectVariant(button));
    });

    document.querySelectorAll('[data-qty-action]').forEach((button) => button.addEventListener('click', () => {
      if (!quantityInput) return;
      const current = Math.max(1, parseInt(quantityInput.value || '1', 10));
      quantityInput.value = button.dataset.qtyAction === 'plus' ? current + 1 : Math.max(1, current - 1);
    }));

    function guideToVariant() {
      if (!variantSection || variantButtons.length <= 1 || selectedVariant) return false;
      if (variantHelp) variantHelp.textContent = 'Choisissez une option pour continuer';
      variantSection.classList.remove('is-highlighted', 'needs-attention');
      void variantSection.offsetWidth;
      variantSection.classList.add('is-highlighted', 'needs-attention');
      const headerHeight = document.getElementById('siteHeader')?.getBoundingClientRect().height || 0;
      const targetY = variantSection.getBoundingClientRect().top + window.scrollY - headerHeight - 28;
      window.scrollTo({ top: Math.max(0, targetY), behavior: prefersReducedMotion ? 'auto' : 'smooth' });
      window.setTimeout(() => variantButtons[0]?.focus({ preventScroll: true }), prefersReducedMotion ? 0 : 380);
      showToast("Choisissez une option avant d'ajouter au panier.", 'error');
      return true;
    }

    function validateVariant() {
      return !guideToVariant();
    }

    function setCartBusy(busy) {
      cartRequestBusy = busy;
      [detailAdd, fixedAdd].forEach((button) => {
        if (!button) return;
        button.setAttribute('aria-busy', busy ? 'true' : 'false');
      });
    }

    async function handleAddToCart(event) {
      event?.preventDefault();
      if (cartRequestBusy || !validateVariant()) return;
      setCartBusy(true);
      const quantity = Math.max(1, parseInt(quantityInput?.value || '1', 10));
      try {
        await addToCart(root.dataset.productSlug, quantity, selectedVariant);
      } finally {
        setCartBusy(false);
      }
    }

    detailAdd?.addEventListener('click', handleAddToCart);
    fixedAdd?.addEventListener('click', handleAddToCart);
    buyNow?.addEventListener('click', (event) => {
      event.preventDefault();
      if (!validateVariant()) return;
      const quantity = Math.max(1, parseInt(quantityInput?.value || '1', 10));
      startStripeCheckout({ source: 'buy_now', slug: root.dataset.productSlug, quantity, variant_id: selectedVariant });
    });

    // Fixed CTA only after the normal CTA has passed behind the sticky header.
    let fixedSyncRaf = 0;
    function syncFixedCta() {
      fixedSyncRaf = 0;
      if (!fixedBar || !primaryZone) return;
      const rect = primaryZone.getBoundingClientRect();
      const headerBottom = document.getElementById('siteHeader')?.getBoundingClientRect().bottom || 0;
      const shouldShow = rect.bottom <= headerBottom;
      fixedBar.classList.toggle('is-visible', shouldShow);
      fixedBar.setAttribute('aria-hidden', shouldShow ? 'false' : 'true');
      document.body.classList.toggle('product-fixed-visible', shouldShow);
    }
    function queueFixedSync() {
      if (fixedSyncRaf) return;
      fixedSyncRaf = requestAnimationFrame(syncFixedCta);
    }
    window.addEventListener('scroll', queueFixedSync, { passive: true });
    window.addEventListener('resize', queueFixedSync, { passive: true });
    syncFixedCta();

    // Visual nudge only: the button hit-box never moves.
    if (!prefersReducedMotion) {
      window.setInterval(() => {
        if (document.hidden) return;
        const target = fixedBar?.classList.contains('is-visible') ? fixedAdd : detailAdd;
        const visual = target?.querySelector('.cta-visual');
        if (!target || !visual || target.disabled || target.matches(':active,:focus-visible')) return;
        const rect = target.getBoundingClientRect();
        if (rect.bottom <= 0 || rect.top >= window.innerHeight) return;
        visual.classList.remove('cta-nudge');
        void visual.offsetWidth;
        visual.classList.add('cta-nudge');
        window.setTimeout(() => visual.classList.remove('cta-nudge'), 700);
      }, 6500);
    }

    // --- Reviews: explicit one-tap form toggle and progressive loading. ---
    const reviewToggle = document.getElementById('reviewFormToggle');
    const reviewPanel = document.getElementById('reviewFormPanel');
    reviewToggle?.addEventListener('click', () => {
      if (!reviewPanel) return;
      const opening = reviewPanel.hidden;
      reviewPanel.hidden = !opening;
      reviewToggle.setAttribute('aria-expanded', opening ? 'true' : 'false');
      reviewToggle.classList.toggle('is-open', opening);
      if (opening) {
        requestAnimationFrame(() => {
          reviewPanel.querySelector('input:not([type="hidden"]),select,textarea')?.focus({ preventScroll: true });
        });
      }
    });

    const reviewList = document.getElementById('reviewList');
    const loadMore = document.getElementById('reviewLoadMore');
    let reviewLoadBusy = false;
    loadMore?.addEventListener('click', async (event) => {
      event.preventDefault();
      if (!reviewList || reviewLoadBusy) return;
      reviewLoadBusy = true;
      loadMore.disabled = true;
      loadMore.setAttribute('aria-busy', 'true');
      const original = loadMore.innerHTML;
      loadMore.innerHTML = '<span class="button-loading-dot" aria-hidden="true"></span> Chargement…';
      try {
        const offset = parseInt(loadMore.dataset.offset || '2', 10);
        const response = await fetch(`${root.dataset.reviewsUrl}?offset=${offset}`, {
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error('Impossible de charger les avis.');
        reviewList.insertAdjacentHTML('beforeend', data.html || '');
        loadMore.dataset.offset = String(data.next_offset || offset);
        if (!data.has_more) {
          loadMore.remove();
        } else {
          loadMore.disabled = false;
          loadMore.removeAttribute('aria-busy');
          loadMore.innerHTML = original;
        }
      } catch (error) {
        loadMore.disabled = false;
        loadMore.removeAttribute('aria-busy');
        loadMore.innerHTML = original;
        showToast(error.message || 'Impossible de charger les avis.', 'error');
      } finally {
        reviewLoadBusy = false;
      }
    });

    document.getElementById('reviewForm')?.addEventListener('submit', async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      if (form.dataset.submitting === '1') return;
      form.dataset.submitting = '1';
      const submit = form.querySelector('[type="submit"]');
      const original = submit?.innerHTML || '';
      if (submit) {
        submit.disabled = true;
        submit.textContent = 'Envoi…';
      }
      try {
        const response = await fetch('/api/submit-review/', {
          method: 'POST',
          headers: { 'X-CSRFToken': getCookie('csrftoken') },
          body: new FormData(form),
        });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.message || 'Formulaire invalide.');
        showToast(data.message, 'success');
        form.reset();
        if (reviewPanel) reviewPanel.hidden = true;
        reviewToggle?.setAttribute('aria-expanded', 'false');
      } catch (error) {
        showToast(error.message || 'Impossible d’envoyer votre avis pour le moment.', 'error');
      } finally {
        form.dataset.submitting = '0';
        if (submit) {
          submit.disabled = false;
          submit.innerHTML = original;
        }
      }
    });

    document.addEventListener('keydown', (event) => {
      if (!lightbox?.classList.contains('open')) return;
      if (event.key === 'Escape') closeLightbox();
      if (event.key === 'ArrowLeft') lightboxSlider?.prev();
      if (event.key === 'ArrowRight') lightboxSlider?.next();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initProductDetail, { once: true });
  } else {
    initProductDetail();
  }
})();
