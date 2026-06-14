function selectColor(id){
            var color = document.getElementById(id)
            console.log("id couleur: "+ color.id);
            document.querySelectorAll(".color .color-display").forEach((color )=> {
                color.classList.remove("active")
                color.innerHTML = '';
            })
            color.classList.add("active");
            document.querySelector(".color-display.active").innerHTML = '<i id="checkIcon" class="bi bi-check-circle-fill text-primary"></i>';
            document.querySelector("#add-form").setAttribute('data-color', color.id)
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
hamburger.addEventListener('click', () =>{
    console.log('affichage du menu')
    navbar.classList.toggle("active");
    hamburger.classList.toggle("active")
})

const pageItem = document.querySelector(".page-item.active")
const pageLink = document.querySelector(".page-link")
if (pageItem){
    pageLink.style.CSSText= "background-color:black; color:white;"
}


  const reviewForm = document.getElementById("review-form");
  // if (!reviewForm){
  //   return;
  // }

  console.log("Formulaire review trouvé");

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
          window.location.href = data.redirect_url + "#review-list";
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
// console.log(Updcart)
Updcart.forEach((button) =>{

    button.addEventListener('click', async function (e) {
    e.preventDefault();
    const action = button.getAttribute("action");
    const itemId = button.getAttribute('data-id')
    console.log("action: ", action, " item_id", itemId)
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

        window.location.reload();
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
      // e.preventDefault();
      
      
      const quantity = document.getElementById("id_quantity").value;
      const url = document.getElementById("add-form").getAttribute('action');
      const color = document.getElementById("add-form").getAttribute('data-color')
      console.log("couleur : " + color + "quantité : "+ quantity)

          try{
            showLoading();
            fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
          },
          body: JSON.stringify({
            quantity: quantity,
            color: color,
          }),
        })
        // .then(response => response.json())
        .then(data => {console.log('Ajouté')})
        .then(response => {console.log('Ajouté: '+ response)})
        hideLoading()
    }catch(error){
      console.log("erreur")
    }finally{
      hideLoading()
    }

     });
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


// review






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
