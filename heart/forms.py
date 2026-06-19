from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field
from .models import *
from django.urls import reverse
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import get_user_model

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'message', 'profil']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Votre message...'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        # self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Envoyer', css_class='btn btn-primary'))


class AddtoCartForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity']
        
    def __init__(self, *args, **kwargs):
        slug = kwargs.pop('slug', None)
        super().__init__(*args, **kwargs)
        self.fields['quantity']
        self.helper = FormHelper()
        if slug:
            self.helper.form_action = reverse('add_to_cart', args=[slug])
        self.helper.layout = Layout(Field('quantity'),
        Submit('submit', 'Add to cart', css_class='addBtn', css_id="add"))


class CartForm(forms.ModelForm):
    class Meta:
        model = Cart
        fields = ['code_promo']
        widgets = {
            'code_promo': forms.Textarea(attrs={'rows': 1, 'placeholder': 'Votre code promo...'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['code_promo']
        self.helper = FormHelper()
        self.helper.layout = Layout(Field('code_promo'), Submit('submit', 'obtenir réduction', css_class='addBt'))


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["name", "image", "rating", "comment"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={
                "accept": "image/*",
                "class": "review-image-upload"
            }),
            "name": forms.TextInput(attrs={
                "placeholder": "Votre nom"
            }),
            "rating": forms.Select(
                choices=[(1, "1 étoile"), (2, "2 étoiles"), (3, "3 étoiles"), (4, "4 étoiles"), (5, "5 étoiles")],
                attrs={"class": "star-rating-select"}
            ),
            "comment": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "Décrivez votre expérience avec ce produit...",
                "class": "comment",
            }),
        }
    
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.form_method = "post"
            self.helper.add_input(Submit("submit", "Envoyer", css_class="btn btn-primary"))
