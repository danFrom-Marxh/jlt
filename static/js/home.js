document.addEventListener('DOMContentLoaded', () => {
  initFlashMessages();
  initSortSelect();
  initProductTilt();
  initQuickViewHoverState();
  initFaqAccessibility();
});

/* =========================
   FLASH MESSAGES
========================= */
function initFlashMessages() {
  const messages = document.getElementById('messages');
  if (!messages) return;

  requestAnimationFrame(() => {
    messages.style.opacity = '1';
    messages.style.transform = 'translateY(0)';
  });

  setTimeout(() => {
    messages.style.opacity = '0';
    messages.style.transform = 'translateY(-8px)';
  }, 3200);
}

/* =========================
   SORT SELECT
========================= */
function initSortSelect() {
  const sortSelect = document.getElementById('sortSelect');
  if (!sortSelect) return;

  sortSelect.addEventListener('change', () => {
    const selectedOption = sortSelect.options[sortSelect.selectedIndex];
    const selectedValue = selectedOption.dataset.url || sortSelect.value;

    const url = new URL(window.location.href);
    url.searchParams.set('sort', selectedValue);
    url.searchParams.delete('page');
    window.location.href = url.toString();
  });
}

/* =========================
   PRODUCT TILT
========================= */
function initProductTilt() {
  const isDesktop = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  if (!isDesktop) return;

  const productCards = document.querySelectorAll('.home-page .product-card');

  productCards.forEach((card) => {
    let frameId = null;

    const resetCard = () => {
      card.style.transform = 'translateY(0)';
    };

    const onMove = (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const rotateY = ((x / rect.width) - 0.5) * 5.5;
      const rotateX = ((y / rect.height) - 0.5) * -5.5;

      if (frameId) cancelAnimationFrame(frameId);

      frameId = requestAnimationFrame(() => {
        card.style.transform = `
          perspective(1000px)
          rotateX(${rotateX}deg)
          rotateY(${rotateY}deg)
          translateY(-4px)
        `;
      });
    };

    const onLeave = () => {
      if (frameId) cancelAnimationFrame(frameId);
      resetCard();
    };

    card.addEventListener('mousemove', onMove);
    card.addEventListener('mouseleave', onLeave);
  });
}

/* =========================
   QUICK VIEW UI STATE
========================= */
function initQuickViewHoverState() {
  const quickButtons = document.querySelectorAll('.home-page .quick-view');

  quickButtons.forEach((button) => {
    button.addEventListener('click', (e) => {
      e.preventDefault();
      const card = button.closest('.product-card');
      const link = card?.querySelector('.product-info h3 a');

      if (link) {
        window.location.href = link.href;
      }
    });
  });
}

/* =========================
   FAQ ACCESSIBILITY
========================= */
function initFaqAccessibility() {
  const faqItems = document.querySelectorAll('.home-page .faq-item');

  faqItems.forEach((item) => {
    item.addEventListener('toggle', () => {
      if (!item.open) return;

      faqItems.forEach((other) => {
        if (other !== item) {
          other.open = false;
        }
      });
    });
  });
}
