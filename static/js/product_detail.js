  document.addEventListener('DOMContentLoaded', () => {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    function activateTab(targetSelector) {
      const target = document.querySelector(targetSelector);
      if (!target) return;

      tabButtons.forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.target === targetSelector);
      });

      tabContents.forEach((content) => {
        content.classList.toggle('active', '#' + content.id === targetSelector);
      });
    }

    tabButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        activateTab(btn.dataset.target);
      });
    });

    if (window.location.hash === '#reviews-content') {
      activateTab('#reviews-content');
    }

  

    const mainImageContainer = document.getElementById('mainImageContainer');
    const carouselTrack = document.getElementById('carouselTrack');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const currentIndexEl = document.getElementById('currentIndex');
    const mainThumbnailsContainer = document.getElementById('mainThumbnails');
    const mainThumbnails = mainThumbnailsContainer
      ? mainThumbnailsContainer.querySelectorAll('.thumbnail')
      : [];

    const fullscreenModal = document.getElementById('fullscreenModal');
    const fullscreenImage = document.getElementById('fullscreenImage');
    const closeFullscreen = document.getElementById('closeFullscreen');
    const prevFullscreenBtn = document.getElementById('prevFullscreen');
    const nextFullscreenBtn = document.getElementById('nextFullscreen');
    const fullscreenCurrentIndex = document.getElementById('fullscreenCurrentIndex');
    const fullscreenThumbnailsContainer = document.getElementById('fullscreenThumbnails');
    const fullscreenThumbs = fullscreenThumbnailsContainer
      ? fullscreenThumbnailsContainer.querySelectorAll('.fullscreen-thumb')
      : [];

    const slides = carouselTrack ? carouselTrack.querySelectorAll('.carousel-slide img') : [];
    const totalImages = slides.length;

    let currentImageIndex = 0;

    if (!carouselTrack || !mainImageContainer || totalImages === 0) {
      return;
    }

    function updateMainCounter() {
      if (currentIndexEl) {
        currentIndexEl.textContent = currentImageIndex + 1;
      }
    }

    function updateFullscreenCounter() {
      if (fullscreenCurrentIndex) {
        fullscreenCurrentIndex.textContent = currentImageIndex + 1;
      }
    }

    function updateMainThumbnails() {
      mainThumbnails.forEach((thumb, i) => {
        thumb.classList.toggle('active', i === currentImageIndex);
      });

      const activeThumb = mainThumbnails[currentImageIndex];

    }

    function updateFullscreenThumbnails() {
      fullscreenThumbs.forEach((thumb, i) => {
        thumb.classList.toggle('active', i === currentImageIndex);
      });

      const activeThumb = fullscreenThumbs[currentImageIndex];
      if (activeThumb) {
        activeThumb.scrollIntoView({
          behavior: 'smooth',
          inline: 'center',
          block: 'nearest'
        });
      }
    }

    function renderCarousel(animate = true) {
      carouselTrack.style.transition = animate ? 'transform 0.35s ease' : 'none';
      carouselTrack.style.transform = `translate3d(-${currentImageIndex * 100}%, 0, 0)`;
      updateMainCounter();
      updateMainThumbnails();

      if (fullscreenModal && fullscreenModal.classList.contains('active')) {
        renderFullscreen();
      }
    }

    function goToSlide(index, animate = true) {
      if (currentImageIndex >= totalImages){
        currentImageIndex = totalImages
      }
      else if(currentImageIndex <= 0){
        currentImageIndex = 0
      }
        currentImageIndex = (index + totalImages) % totalImages;
        renderCarousel(animate);
    }

    function nextSlide() {
      goToSlide(currentImageIndex + 1);
    }

    function prevSlide() {
      goToSlide(currentImageIndex - 1);
    }

    function renderFullscreen() {
      if (!fullscreenImage || !slides[currentImageIndex]) return;
      fullscreenImage.src = slides[currentImageIndex].src;
      fullscreenImage.alt = slides[currentImageIndex].alt || 'Image produit';
      updateFullscreenCounter();
      updateFullscreenThumbnails();
    }

    function openFullscreen(index = currentImageIndex) {
      if (!fullscreenModal || !fullscreenImage) return;
      currentImageIndex = index;
      renderCarousel(false);
      renderFullscreen();
      fullscreenModal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }

    function closeFullscreenModal() {
      if (!fullscreenModal) return;
      fullscreenModal.classList.remove('active');
      document.body.style.overflow = '';
    }

    if (prevBtn) prevBtn.addEventListener('click', prevSlide);
    if (nextBtn) nextBtn.addEventListener('click', nextSlide);

    mainThumbnails.forEach((thumb, index) => {
      thumb.addEventListener('click', () => {
        goToSlide(index);
      });
    });

    if (mainImageContainer) {
      mainImageContainer.addEventListener('click', (e) => {
        if (e.target.closest('.carousel-btn')) return;
        if (dragState.hasMoved) return;
        openFullscreen(currentImageIndex);
      });
    }

    if (prevFullscreenBtn) prevFullscreenBtn.addEventListener('click', prevSlide);
    if (nextFullscreenBtn) nextFullscreenBtn.addEventListener('click', nextSlide);

    fullscreenThumbs.forEach((thumb, index) => {
      thumb.addEventListener('click', () => {
        goToSlide(index);
      });
    });

    if (closeFullscreen) {
      closeFullscreen.addEventListener('click', closeFullscreenModal);
    }

    if (fullscreenModal) {
      fullscreenModal.addEventListener('click', (e) => {
        if (e.target === fullscreenModal) {
          closeFullscreenModal();
        }
      });
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeFullscreenModal();
      if (e.key === 'ArrowLeft') prevSlide();
      if (e.key === 'ArrowRight') nextSlide();
    });

    const dragState = {
      isPointerDown: false,
      isDragging: false,
      isHorizontalGesture: false,
      hasMoved: false,
      startX: 0,
      startY: 0,
      currentDeltaX: 0,
      width: 0
    };

    function getPoint(event) {
      if (event.touches && event.touches.length > 0) {
        return {
          x: event.touches[0].clientX,
          y: event.touches[0].clientY
        };
      }

      if (event.changedTouches && event.changedTouches.length > 0) {
        return {
          x: event.changedTouches[0].clientX,
          y: event.changedTouches[0].clientY
        };
      }

      return {
        x: event.clientX,
        y: event.clientY
      };
    }

    function resetDragState() {
      dragState.isPointerDown = false;
      dragState.isDragging = false;
      dragState.isHorizontalGesture = false;
      dragState.currentDeltaX = 0;

      carouselTrack.classList.remove('dragging');
      carouselTrack.style.transition = 'transform 0.35s ease';
    }

    function onPointerStart(event) {
      if (event.type === 'mousedown' && event.button !== 0) return;

      const point = getPoint(event);

      dragState.isPointerDown = true;
      dragState.isDragging = false;
      dragState.isHorizontalGesture = false;
      dragState.hasMoved = false;
      dragState.startX = point.x;
      dragState.startY = point.y;
      dragState.currentDeltaX = 0;
      dragState.width = mainImageContainer.offsetWidth;

      // Empêcher le scroll pendant le glissement
      if (event.preventDefault) {
        event.preventDefault();
      }
    }

    function onPointerMove(event) {
      if (!dragState.isPointerDown) return;

      const point = getPoint(event);
      const deltaX = point.x - dragState.startX;
      const deltaY = point.y - dragState.startY;

      if (!dragState.isDragging) {
        const absX = Math.abs(deltaX);
        const absY = Math.abs(deltaY);

        if (absX < 8 && absY < 8) return;

        dragState.isDragging = true;
        dragState.isHorizontalGesture = absX > absY;

        if (!dragState.isHorizontalGesture) {
          resetDragState();
          return;
        }

        carouselTrack.classList.add('dragging');
      }

      if (!dragState.isHorizontalGesture) return;

      dragState.hasMoved = true;
      dragState.currentDeltaX = deltaX;

      const baseTranslate = -currentImageIndex * dragState.width;
      let nextTranslate = baseTranslate + deltaX;

      if (currentImageIndex === 0 && deltaX > 0) {
        nextTranslate = baseTranslate + (deltaX * 0.35);
      }

      if (currentImageIndex === totalImages - 1 && deltaX < 0) {
        nextTranslate = baseTranslate + (deltaX * 0.35);
      }

      carouselTrack.style.transition = 'none';
      carouselTrack.style.transform = `translate3d(${nextTranslate}px, 0, 0)`;
    }

    function onPointerEnd() {
      if (!dragState.isPointerDown) return;

      const shouldHandleSlide = dragState.isDragging && dragState.isHorizontalGesture;
      const deltaX = dragState.currentDeltaX;
      const threshold = dragState.width * 0.18;

      resetDragState();

      if (!shouldHandleSlide) return;

      if (deltaX <= -threshold) {
        nextSlide();
      } else if (deltaX >= threshold) {
        prevSlide();
      } else {
        renderCarousel(true);
      }

      window.setTimeout(() => {
        dragState.hasMoved = false;
      }, 50);
    }

    carouselTrack.addEventListener('dragstart', (e) => e.preventDefault());

    carouselTrack.addEventListener('mousedown', onPointerStart);
    window.addEventListener('mousemove', onPointerMove);
    window.addEventListener('mouseup', onPointerEnd);

    carouselTrack.addEventListener('touchstart', onPointerStart, { passive: true });
    carouselTrack.addEventListener('touchmove', onPointerMove, { passive: false });
    carouselTrack.addEventListener('touchend', onPointerEnd, { passive: true });
    carouselTrack.addEventListener('touchcancel', onPointerEnd, { passive: true });

    mainImageContainer.addEventListener(
      'wheel',
      (e) => {
        if (Math.abs(e.deltaX) > Math.abs(e.deltaY) || e.shiftKey) {
          e.preventDefault();
          if (e.deltaX > 0 || e.deltaY > 0) {
            nextSlide();
          } else {
            prevSlide();
          }
        }
      },
      { passive: false }
    );

    renderCarousel(false);
  });


// stars 

document.addEventListener("DOMContentLoaded", function () {
  const container = document.getElementById("starRatingInput");
  const ratingText = document.getElementById("ratingText");

  if (!container) return;

  const inputs = container.querySelectorAll('input[type="radio"]');
  const labels = container.querySelectorAll("label");

  function updateRatingText(value) {
    if (!ratingText) return;
    if (!value) ratingText.textContent = "Sélectionnez une note";
    else ratingText.textContent = value === 1 ? "1 étoile" : value + " étoiles";
  }

  function paintStars(value) {
    labels.forEach((label) => {
      const starValue = parseInt(label.dataset.value, 10);
      label.classList.toggle("filled", starValue <= value);
    });
    updateRatingText(value);
  }

  labels.forEach((label) => {
    const value = parseInt(label.dataset.value, 10);

    label.addEventListener("mouseenter", () => paintStars(value));
    label.addEventListener("click", () => {
      const relatedInput = document.getElementById("star" + value);
      if (relatedInput) relatedInput.checked = true;
      paintStars(value);
    });
  });

  container.addEventListener("mouseleave", () => {
    const checked = container.querySelector('input[type="radio"]:checked');
    paintStars(checked ? parseInt(checked.value, 10) : 0);
  });

  inputs.forEach((input) => {
    input.addEventListener("change", () => paintStars(parseInt(input.value, 10)));
  });

  // Initialisation si valeur déjà sélectionnée
  const checked = container.querySelector('input[type="radio"]:checked');
  paintStars(checked ? parseInt(checked.value, 10) : 0);
});