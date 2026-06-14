// const productCards = document.querySelectorAll('.product-card');

//   productCards.forEach((card) => {
//     card.addEventListener('mousemove', (e) => {
//       const rect = card.getBoundingClientRect();
//       const x = e.clientX - rect.left;
//       const y = e.clientY - rect.top;

//       const rotateY = ((x / rect.width) - 0.5) * 6;
//       const rotateX = ((y / rect.height) - 0.5) * -6;

//       card.style.transform = `perspective(900px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
//     });

//     card.addEventListener('mouseleave', () => {
//       card.style.transform = 'perspective(900px) rotateX(0deg) rotateY(0deg) translateY(0)';
//     });
//   });

  document.addEventListener('DOMContentLoaded', () => {
    const isDesktop = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    const productCards = document.querySelectorAll('.home-page .product-card');

    if (isDesktop) {
      productCards.forEach((card) => {
        card.addEventListener('mousemove', (e) => {
          const rect = card.getBoundingClientRect();
          const x = e.clientX - rect.left;
          const y = e.clientY - rect.top;

          const rotateY = ((x / rect.width) - 0.5) * 6;
          const rotateX = ((y / rect.height) - 0.5) * -6;

          card.style.transform = `perspective(900px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
        });

        card.addEventListener('mouseleave', () => {
          card.style.transform = 'translateY(0)';
        });
      });
    }

    const messages = document.getElementById('messages');
    if (messages) {
      messages.style.opacity = '1';

      setTimeout(() => {
        messages.style.opacity = '0';
      }, 3000);
    }

    const sortSelect = document.getElementById('sortSelect');
    sortSelect?.addEventListener('change', () => {
      const selectedOption = sortSelect.options[sortSelect.selectedIndex];
      const selectedValue = selectedOption.dataset.url || sortSelect.value;

      const url = new URL(window.location.href);
      url.searchParams.set('sort', selectedValue);
      window.location.href = url.toString();
    });
  });


    document.addEventListener('DOMContentLoaded', () => {
        const sortSelect = document.getElementById('sortSelect');
        // var optS = sortSelect.options[sortSelect.selectedIndex];
        sortSelect?.addEventListener('change', () => {
            var optS = sortSelect.options[sortSelect.selectedIndex];
            var urlDest = optS.dataset.url;
            console.log(urlDest);
            if(urlDest){
                const url = new URL(window.location);
                url.searchParams.set('sort', optS.dataset.url);
                console.log(url);
                window.location.href = url.toString();
            }
            else{
                const url = new URL(window.location);
                url.searchParams.set('sort', sortSelect.value );
                console.log(url);
                window.location.href = url.toString();
            }
        });
    });