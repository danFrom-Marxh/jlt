from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('', home, name="home"),
    path('panier/ajouter/<slug:slug>', add_to_cart, name='add_to_cart'),
    path('product/<slug:slug>', product_detail, name='product_detail'),
    path('cart/', cart, name='cart'),
    path('remove_cart', remove_cart, name='remove_cart'),
    path('api/update_cart/', update_cart, name="update_cart"),
    path('services/', TemplateView.as_view(template_name="services.html", extra_context={"salut": "salut"}), name="services"),
    path('apropos/', TemplateView.as_view(template_name="a_propos.html"), name="apropos"),
    path('api/contact/', contact_form_save, name="contact_form_save"),
    path('contact/', contact, name="contact"),
    path('weather/', TemplateView.as_view(template_name="weather.html"), name="weather"),
    path("api/search-city/", search_city, name="search_city"),
    path("api/weather/", city_weather, name="city_weather"),
    path('api/search-autocomplete/', search_autocomplete, name='search_autocomplete'),
    path('recherche/', search_view, name='search'),
    path("api/submit-review/", submit_review, name="submit_review"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)