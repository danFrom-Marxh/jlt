  const contactForm = document.querySelector(".contact-page form");
  contactForm?.addEventListener("submit", async function (e) {
    e.preventDefault();
    console.log("message intercepté");

    const formData = new FormData(contactForm);

    try {
      showLoading?.();

      const response = await fetch("/api/contact/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
        },
      });

    //   console.log("Réponse HTTP :", response.status);

      const data = await response.json();
      console.log("Réponse serveur :", data);

      if (data.success) {
        contacForm.reset();

        if (data.redirect_url) {
          showToast(data.message, "success")
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