  function selectVariante(id) {
  const allVariants = document.querySelectorAll(".variant-card");
  const selected = document.getElementById("var-" + id);
  const addForm = document.getElementById("add-form");

  if (!selected || selected.classList.contains("is-disabled")) {
    return;
  }

  allVariants.forEach((variant) => {
    variant.classList.remove("active");
  });

  selected.classList.add("active");

  if (addForm) {
    addForm.setAttribute("data-variante", id);
  }
}

const messages = document.getElementById("messages");
if(messages){
    messages.style.opacity="1";
        setTimeout(()=>{
        messages.style.opacity="0";
         
    }, 3000)
    setTimeout(()=>{
         messages.style.left="-300px";
    }, 4000)
}


  // menu hamburger
const navbar = document.getElementById("navbar")
const hamburger = document.getElementById("hamburger")
const AddForm = document.querySelector("form .addToCartForm");
const overlay = document.getElementById("menu-overlay");
const searchClose = document.getElementById("search-close");

function closeMenu(){
  overlay.classList.remove("active")
  navbar.classList.toggle("active");
  hamburger.classList.toggle("active")
}

hamburger.addEventListener('click', () =>{
    navbar.classList.toggle("active");
    hamburger.classList.toggle("active")
    overlay.classList.toggle("active");
})

overlay.addEventListener('click', closeMenu);

const pageItem = document.querySelector(".page-item.active")
const pageLink = document.querySelector(".page-link")
if (pageItem){
    pageLink.style.CSSText= "background-color:black; color:white;"
}


  const reviewForm = document.getElementById("review-form");
  // if (!reviewForm){
  //   return;
  // }

  reviewForm?.addEventListener("submit", async function (e) {
    e.preventDefault();
    console.log("submit intercepté");

    const selectedRate = reviewForm.querySelector('input[name="rating"]:checked');
    if (!selectedRate) {
      alert("Veuillez sélectionner une note.");
      return;
    }

    const formData = new FormData(reviewForm);

    try {
      showLoading?.();

      const response = await fetch("/api/submit-review/", {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "XMLHttpRequest"
        },
        body: formData
      });

      console.log("Réponse HTTP :", response.status);

      const data = await response.json();
      console.log("Réponse serveur :", data);

      if (data.success) {
        // alert(data.message || "Avis enregistré.");
        reviewForm.reset();

        if (data.redirect_url) {
          // window.location.href = data.redirect_url + "#review-list";
          showToast(" Merci pour votre commentaire nous allons le lire et l'approuver", "success")
        }
      } else {
        alert(data.message || "Erreur lors de l'enregistrement.");
        console.log(data.errors || {});
      }
    } catch (error) {
      console.error("Erreur submit review :", error);
      alert("Une erreur JS ou réseau est survenue.");
    } finally {
      hideLoading?.();
    }
  });

const getCookie = (name) => {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
};

const csrftoken = getCookie("csrftoken");

const Updcart = document.querySelectorAll(".cart-content #update_cart")
Updcart.forEach((button) =>{
    button.addEventListener('click', async function (e) {
      // showLoading();
    e.preventDefault();
    const itemCount = document.querySelectorAll(".item-details #item_count");
    const action = button.getAttribute("action");
    const itemId = button.getAttribute('data-id')
    const badge = document.getElementById("badge");
    const subTotal = document.querySelectorAll(".item-actions .item-subtotal");
    const totalPrice = document.getElementById('prix_total');
    const nbItem = document.getElementById("nb_item");
    const response = await fetch("/api/update_cart/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
          },
          body: JSON.stringify({
            action: action,
            item_id: itemId,
          }),
        });
        const data = await response.json()
        if (data.success){
          console.log("succès : ", data.success, ", quantité item : ",  data.item_count)
          if(data.item_deleted){
            window.location.reload();
        }

          itemCount.forEach((itemC, i) =>{
            if (itemC.getAttribute("data-cart_item_id") == data.item_id && subTotal[i].getAttribute("data-cart_item_id") == data.item_id){
              itemC.textContent = "(" + data.item_count + ")";
              badge.textContent = data.panier;
              subTotal[i].innerHTML = data.item_prix_total + "<b> GBP</b>";
              totalPrice.innerHTML ="Total : "+ `${data.prix_total}` + "<b> GBP </b>";
              nbItem.textContent = "(" + data.panier + ")" + " items |";
            }

            hideLoading();
          });
          
        }
        else{
          console.log("success : ", data.success, "quantité panier : ", data.panier)
          showToast(data.message, "error");
          itemCount.textContent = "(" + data.item_count + ")"
          hideLoading();
        }

})
})

// Search Overlay
document.getElementById("search-btn")?.addEventListener("click", () => {
  document.getElementById("search-overlay").classList.remove("hidden");
  document.getElementById("search-input").focus();
});

document.getElementById("close-search")?.addEventListener("click", () => {
  document.getElementById("search-overlay").classList.add("hidden");
});

function closeSearch(){
  document.getElementById("search-overlay").classList.add("hidden");
  searchClose.classList.toggle("hidden");
}

searchClose.addEventListener('click', closeSearch);

// Search Autocomplete
let searchTimeout;
document.getElementById("search-input")?.addEventListener("input", function () {
  const query = this.value;

  if (query.length < 2) {
    document.getElementById("autocomplete-results").innerHTML = "";
    return;
  }

  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    fetch(`/api/search-autocomplete/?q=${encodeURIComponent(query)}`)
      .then((res) => res.json())
      .then((data) => {
        const resultsDiv = document.getElementById("autocomplete-results");
        resultsDiv.innerHTML = "";

        if (data.results.length === 0) {
          resultsDiv.innerHTML =
            '<p style="padding: 15px; text-align: center; color: #7f8c8d;">Aucun résultat trouvé</p>';
          return;
        }

        data.results.forEach((product) => {
          const item = document.createElement("a");
          item.href = `/product/${product.slug}`;
          item.className = "autocomplete-item";
          item.innerHTML = `
                        ${product.image ? `<img src="${product.image}" alt="${product.name}">` : ""}
                        <div class="autocomplete-item-info">
                            <h4>${product.name}</h4>
                            <p>${product.price.toLocaleString("fr-FR")} FCFA</p>
                        </div>
                    `;
          resultsDiv.appendChild(item);
        });
      });
  }, 300);
});

    document.querySelector("form .addBtn").addEventListener("click", async function (e) {
      e.preventDefault();
      showLoading();
      const quantity = document.getElementById("id_quantity").value;
      const url = document.getElementById("add-form").getAttribute('action');
      const variante = document.getElementById("add-form").getAttribute('data-variante')

      if(!variante){
        showToast("vous devez selectionner une variante", "error");
        document.getElementById("var-ob").textContent = "!!! vous devez selectionner une variante !!!";
        
        setTimeout(function(){
          document.getElementById("var-ob").textContent = "";
        }, 2000)
        hideLoading();
      }

      else{
        const badge = document.getElementById("badge");
      console.log("id_variante : " + variante + ", quantité : "+ quantity)

      try{
          const response = await fetch(url,{
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
          },
          body: JSON.stringify({
            quantity: quantity,
            variante: variante,
          }),
        })
       const data = await response.json();

        if (data.success) {
          console.log("succès : ", data.success, ", quantité panier : ",  data.panier)
          showToast(data.message, "success");
          badge.textContent = data.panier;
        } else {
          console.log("success : ", data.success, "quantité panier : ", data.panier)
          showToast(data.message, "error");
        }
      } catch (error) {
        console.error("Error:", error);
        showToast("Une erreur est survenue", "error");
      } finally {
        hideLoading();
      }
      }
    });


// Fonction pour afficher un toast/notification
  function showToast(message, type = 'info') {
    // Si un système de toast existe déjà, l'utiliser
    // if (typeof window.showToast === 'function') {
    //   window.showToast(message, type);
    //   return;
    // }
    
    // Créer un toast simple
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      padding: 12px 20px;
      border-radius: 4px;
      color: white;
      font-size: 16px;
      z-index: 10000;
      box-shadow: 0 3px 6px rgba(0,0,0,0.16);
      animation: fadeInUp 0.3s, fadeOut 0.3s 2.7s forwards;
    `;
    
    // Définir la couleur selon le type
    const colors = {
      success: '#4CAF50',
      error: '#F44336',
      warning: '#FF9800',
      info: '#2196F3'
    };
    toast.style.backgroundColor = colors[type] || colors.info;
    
    // Ajouter le CSS pour l'animation si nécessaire
    if (!document.getElementById('toast-animations')) {
      const style = document.createElement('style');
      style.id = 'toast-animations';
      style.textContent = `
        @keyframes fadeInUp {
          from { opacity: 0; transform: translate(-50%, 20px); }
          to { opacity: 1; transform: translate(-50%, 0); }
        }
        @keyframes fadeOut {
          from { opacity: 1; }
          to { opacity: 0; }
        }
      `;
      document.head.appendChild(style);
    }
    
    document.body.appendChild(toast);
    
    // Supprimer après 3 secondes
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 3000);
  }


    // Notification System
// function showNotification(message, type = "info") {
//   const notification = document.createElement("div");
//   notification.className = `notification notification-${type}`;
//   notification.textContent = message;
//   notification.style.cssText = `
//         position: fixed;
//         top: 20px;
//         left: 20px;
//         padding: 25px 25px;
//         background: ${type === "success" ? "rgba(28, 177, 80, 1)" : type === "error" ? "#e74c3c" : "#3498db"};
//         color: white;
//         border-radius: 8px;
//         box-shadow: 0 4px 12px rgba(0,0,0,0.15);
//         z-index: 10000;
//         animation: slideIn 0.3s ease;
//         opacity: 1;
//         animation: slideInLeft 0.3s ease;
//     `;
//   document.body.appendChild(notification);
//   setTimeout(() => {
//      notification.style.opacity = "0"; 
//     notification.style.animation = "slideOut 0.3s ease";
//     setTimeout(() =>notification.remove(), 300);
//   }, 3000);
// }


// Partners Carousel Enhanced

class PartnersCarousel {
  constructor() {
    this.carousel = document.getElementById("partners-carousel");
    if (!this.carousel) return;

    this.init();
  }

  init() {
    // Clone les éléments pour un défilement infini fluide
    const partners = this.carousel.querySelectorAll(".partner-item");
    partners.forEach((partner) => {
      const clone = partner.cloneNode(true);
      this.carousel.appendChild(clone);
    });

    // Pause au survol
    this.carousel.addEventListener("mouseenter", () => {
      this.carousel.style.animationPlayState = "paused";
    });

    this.carousel.addEventListener("mouseleave", () => {
      this.carousel.style.animationPlayState = "running";
    });
  }
}

// Initialiser
document.addEventListener("DOMContentLoaded", () => {
  new PartnersCarousel();
});

    const toggleCommentsBtn = document.getElementById('toggleComments');

      // ========== COMMENTAIRES "VOIR PLUS" ==========
    if (toggleCommentsBtn) {
        let expanded = false;
        toggleCommentsBtn.addEventListener('click', function() {
            const hiddenComments = document.querySelectorAll('.hidden-comment');
            hiddenComments.forEach(function(comment) {
                if (expanded) {
                    comment.style.display = 'none';
                } else {
                    comment.style.display = 'block';
                }
            });
            expanded = !expanded;
            this.textContent = expanded ? 'Voir moins de commentaires' : 'Voir plus de commentaires';
        });
    }
    
    // ========== SUPPRIMER COMMENTAIRE ==========
    document.querySelectorAll('.delete-comment-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const commentId = this.getAttribute('data-comment-id');
            
            if (confirm('Voulez-vous vraiment supprimer ce commentaire ?')) {
                const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                
                fetch('/comment/' + commentId + '/delete/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrftoken
                    }
                })
                .then(function(response) {
                    return response.json();
                })
                .then(function(data) {
                    if (data.success) {
                        window.location.reload();
                    } else {
                        alert('Actualisez la page pour supprimer.');
                    }
                })
                .catch(function(error) {
                    console.error('Error:', error);
                    alert('Actualisez la page pour supprimer.');
                });
            }
        });
    });
