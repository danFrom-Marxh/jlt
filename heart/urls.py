from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.urls import path
from django.views.generic import RedirectView, TemplateView

from .sitemaps import CategorySitemap, ProductSitemap, StaticViewSitemap
from .views import *

sitemaps = {
    "static": StaticViewSitemap,
    "products": ProductSitemap,
    "categories": CategorySitemap,
}

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('', home, name='home'),
    path('boutique/', catalog, name='catalog'),
    path('categorie/<slug:slug>/', category_products, name='category_products'),
    path('produit/<slug:slug>/', product_detail, name='product_detail'),
    path('product/<slug:slug>/', RedirectView.as_view(pattern_name='product_detail', permanent=True)),
    path('product/<slug:slug>', RedirectView.as_view(pattern_name='product_detail', permanent=True)),
    path('api/produit/<slug:slug>/avis/', product_reviews_more, name='product_reviews_more'),
    path('panier/', cart, name='cart'),
    path('cart/', RedirectView.as_view(pattern_name='cart', permanent=True)),
    path('panier/ajouter/<slug:slug>/', add_to_cart, name='add_to_cart'),
    path('panier/ajouter/<slug:slug>', add_to_cart),
    path('remove_cart', remove_cart, name='remove_cart'),
    path('api/update_cart/', update_cart, name='update_cart'),
    path('api/cart/summary/', cart_summary, name='cart_summary'),
    path('api/checkout/stripe/', create_checkout_session, name='create_checkout_session'),
    path('paiement/succes/', checkout_success, name='checkout_success'),
    path('paiement/annule/', checkout_cancel, name='checkout_cancel'),
    path('api/stripe/webhook/', stripe_webhook, name='stripe_webhook'),
    path('services/', TemplateView.as_view(template_name='services.html'), name='services'),
    path('apropos/', TemplateView.as_view(template_name='a_propos.html'), name='apropos'),
    path('api/contact/', contact_form_save, name='contact_form_save'),
    path('contact/', contact, name='contact'),
    path('weather/', TemplateView.as_view(template_name='weather.html'), name='weather'),
    path('api/search-city/', search_city, name='search_city'),
    path('api/weather/', city_weather, name='city_weather'),
    path('api/search-autocomplete/', search_autocomplete, name='search_autocomplete'),
    path('recherche/', search_view, name='search'),
    path('api/newsletter/subscribe/', newsletter_subscribe, name='newsletter_subscribe'),
    path('api/submit-review/', submit_review, name='submit_review'),
    path('tout_les_messages/', tout_les_messages, name='tout_les_messages'),
    path('delete_message/', supprimer_message, name='delete_message'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
