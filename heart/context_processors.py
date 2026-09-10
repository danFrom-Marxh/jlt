import json

from django.conf import settings
from django.db.models import Sum
from django.templatetags.static import static
from django.urls import reverse

from .models import Cart, Category


def _json_for_script(data):
    return (json.dumps(data, ensure_ascii=False)
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026"))


def store_context(request):
    """Small, safe store + SEO context available on every page."""
    cart_count = 0
    try:
        # Lecture seule : ne créons pas de session/panier pour un visiteur ou un robot
        # qui ne fait que consulter une page. Le panier est créé au premier vrai besoin.
        cart = None
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        elif request.session.session_key:
            cart = Cart.objects.filter(session_key=request.session.session_key, user=None).first()
        if cart:
            cart_count = cart.items.aggregate(total=Sum("quantity"))["total"] or 0
    except Exception:
        cart = None

    store_name = getattr(settings, "STORE_NAME", "Just Like That")
    site_description = getattr(settings, "SITE_DESCRIPTION", "")
    canonical_url = request.build_absolute_uri(request.path)
    page_number = request.GET.get("page", "").strip()
    if page_number.isdigit() and int(page_number) > 1:
        canonical_url = f"{canonical_url}?page={int(page_number)}"
    home_url = request.build_absolute_uri(reverse("home"))
    logo_url = request.build_absolute_uri(static("brand/logo-512.png"))
    social_image_url = request.build_absolute_uri(static("brand/og-default.png"))
    search_target = request.build_absolute_uri(reverse("search")) + "?q={search_term_string}"

    organization_schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": store_name,
        "url": home_url,
        "logo": logo_url,
    }
    if getattr(settings, "SUPPORT_EMAIL", ""):
        organization_schema["email"] = settings.SUPPORT_EMAIL

    website_schema = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": store_name,
        "url": home_url,
        "potentialAction": {
            "@type": "SearchAction",
            "target": search_target,
            "query-input": "required name=search_term_string",
        },
    }

    return {
        "cart_items_count": cart_count,
        "nav_categories": Category.objects.all()[:8],
        "store_currency_symbol": getattr(settings, "STORE_CURRENCY_SYMBOL", "€"),
        "store_name": store_name,
        "store_address": getattr(settings, "STORE_ADDRESS", ""),
        "google_maps_embed_api_key": getattr(settings, "GOOGLE_MAPS_EMBED_API_KEY", ""),
        "site_description": site_description,
        "canonical_url": canonical_url,
        "default_social_image_url": social_image_url,
        "organization_schema_json": _json_for_script(organization_schema),
        "website_schema_json": _json_for_script(website_schema),
    }
