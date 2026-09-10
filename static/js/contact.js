const contactForm=document.querySelector('.contact-page form');
contactForm?.addEventListener('submit',async event=>{
  event.preventDefault();
  const status=document.getElementById('contactFormStatus');
  const submit=contactForm.querySelector('[type="submit"]');
  if(status)status.textContent='Envoi en cours…';
  if(submit)submit.disabled=true;
  try{
    showLoading?.();
    const response=await fetch('/api/contact/',{method:'POST',headers:{'X-Requested-With':'XMLHttpRequest','X-CSRFToken':getCookie('csrftoken')},body:new FormData(contactForm)});
    const data=await response.json();
    if(!response.ok||!data.success)throw new Error(data.message||'Vérifiez les informations du formulaire.');
    contactForm.reset();
    if(status)status.textContent='Votre message a bien été envoyé.';
    showToast(data.message||'Votre message a bien été envoyé.','success');
  }catch(error){
    if(status)status.textContent=error.message||'Impossible d’envoyer le message.';
    showToast(error.message||'Impossible d’envoyer le message.','error');
  }finally{hideLoading?.();if(submit)submit.disabled=false;}
});
