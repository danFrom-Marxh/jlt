import json
import logging
from decimal import Decimal, ROUND_HALF_UP

import requests
import stripe
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.db.models import Avg, Count, OuterRef, Prefetch, Q, Subquery, Sum
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.html import escape, strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .forms import CartForm, ContactForm, ReviewForm
from .models import (
    Cart,
    CartItem,
    Category,
    Contact,
    PaymentRecord,
    Product,
    ProductImage,
    ProductVariant,
    Review,
    SaleItem,
    NewsletterSubscriber,
)

logger = logging.getLogger(__name__)

API_KEY = settings.OPENWEATHERMAP_API_KEY
GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


@require_GET
def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse("sitemap"))
    body = f"User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /panier/\nDisallow: /recherche/\nSitemap: {sitemap_url}\n"
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


@require_GET
def health_check(request):
    """Render readiness probe: verifies that Django can reach the database."""
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "unhealthy"}, status=503)
    return JsonResponse({"status": "ok"})


@require_GET
def search_city(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"results": []})
    try:
        response = requests.get(GEOCODING_URL, params={"q": query, "limit": 5, "appid": API_KEY}, timeout=10)
        response.raise_for_status()
        return JsonResponse({"results": [
            {"name": i.get("name"), "country": i.get("country"), "state": i.get("state", ""), "lat": i.get("lat"), "lon": i.get("lon")}
            for i in response.json()
        ]})
    except requests.RequestException as exc:
        return JsonResponse({"error": str(exc)}, status=500)


@require_GET
def city_weather(request):
    lat, lon = request.GET.get("lat"), request.GET.get("lon")
    if not lat or not lon:
        return JsonResponse({"error": "Paramètres lat et lon requis."}, status=400)
    try:
        current = requests.get(WEATHER_URL, params={"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric", "lang": "fr"}, timeout=10)
        forecast = requests.get(FORECAST_URL, params={"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric", "lang": "fr"}, timeout=10)
        current.raise_for_status(); forecast.raise_for_status()
        return JsonResponse({"current": current.json(), "forecast": forecast.json()})
    except requests.RequestException as exc:
        return JsonResponse({"error": str(exc)}, status=500)


def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key, user=None)
    return cart


def _store_products():
    """Queryset commun aux vitrines, sans N+1 ni chargement massif des avis."""
    review_stats = (
        Review.objects.filter(product_id=OuterRef("pk"), status="approved")
        .values("product_id")
        .annotate(avg_rating=Avg("rating"), review_total=Count("id"))
    )
    return (
        Product.objects.select_related("category")
        .annotate(
            store_average_rating=Subquery(review_stats.values("avg_rating")[:1]),
            store_review_count=Subquery(review_stats.values("review_total")[:1]),
        )
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.select_related("color").order_by("order"),
            ),
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.select_related("color", "size").order_by("id"),
            ),
        )
    )


def _ordered_products_from_sales(limit=8):
    ranked = list(
        SaleItem.objects.filter(payment__status="paid")
        .values("product_id")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:limit]
    )
    if not ranked:
        return [], False
    ids = [row["product_id"] for row in ranked]
    products = {str(p.id): p for p in _store_products().filter(id__in=ids)}
    ordered = [products[str(i)] for i in ids if str(i) in products]
    return ordered, bool(ordered)


def _recommended_products(seed_products, limit=8):
    """Recommandations en nombre fixe de requêtes, sans requête par produit.

    Priorité aux produits réellement achetés dans les mêmes commandes, puis aux
    produits des mêmes catégories. Le chargement final passe une seule fois par
    ``_store_products`` pour précharger images et variantes, et annoter les notes.
    """
    seeds = [product for product in seed_products if product is not None]
    seed_ids = {product.id for product in seeds}
    if not seed_ids:
        return []

    payment_ids = (
        SaleItem.objects.filter(payment__status="paid", product_id__in=seed_ids)
        .values("payment_id")
    )
    ranked_ids = [
        row["product_id"]
        for row in (
            SaleItem.objects.filter(payment_id__in=Subquery(payment_ids))
            .exclude(product_id__in=seed_ids)
            .values("product_id")
            .annotate(recommendation_score=Sum("quantity"))
            .order_by("-recommendation_score")[: limit * 2]
        )
    ]

    category_ids = {product.category_id for product in seeds if product.category_id}
    fallback_qs = Product.objects.exclude(id__in=seed_ids)
    if category_ids:
        fallback_qs = fallback_qs.filter(category_id__in=category_ids)
    fallback_ids = list(
        fallback_qs.exclude(id__in=ranked_ids)
        .order_by("-is_featured", "-created_at")
        .values_list("id", flat=True)[: limit * 2]
    )

    ordered_ids = []
    seen = set(seed_ids)
    for product_id in [*ranked_ids, *fallback_ids]:
        if product_id in seen:
            continue
        seen.add(product_id)
        ordered_ids.append(product_id)
        if len(ordered_ids) >= limit:
            break

    if not ordered_ids:
        return []
    products_by_id = {product.id: product for product in _store_products().filter(id__in=ordered_ids)}
    return [products_by_id[product_id] for product_id in ordered_ids if product_id in products_by_id]


def home(request):
    products = _store_products()
    categories = Category.objects.annotate(product_count=Count("cat")).order_by("name")
    newest = list(products.order_by("-created_at")[:8])
    featured = list(products.filter(is_featured=True).order_by("-created_at")[:8]) or newest[:8]
    loved = list(
        products.annotate(
            avg_score=Avg("reviews__rating", filter=Q(reviews__status="approved")),
            review_total=Count("reviews", filter=Q(reviews__status="approved")),
        ).order_by("-avg_score", "-review_total", "-created_at")[:8]
    )
    bestsellers, has_sales = _ordered_products_from_sales()
    if not bestsellers:
        bestsellers = list(
            products.annotate(demand=Sum("cartitem__quantity")).order_by("-demand", "-created_at")[:8]
        )
    home_reviews = list(
        Review.objects.filter(status="approved")
        .exclude(comment__exact="")
        .select_related("product")
        .order_by("-created_at")[:10]
    )
    return render(request, "home.html", {
        "categories": categories,
        "newest_products": newest,
        "featured_products": featured,
        "loved_products": loved,
        "bestseller_products": bestsellers,
        "bestseller_title": "Les plus achetés" if has_sales else "Les plus demandés",
        "home_reviews": home_reviews,
        "product_count": Product.objects.count(),
        "review_count": Review.objects.filter(status="approved").count(),
    })


def catalog(request, category_slug=None):
    products = _store_products()
    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=active_category)

    query = request.GET.get("q", "").strip()[:200]
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query) |
            Q(description_detaillee__icontains=query) | Q(category__name__icontains=query)
        )

    sort = request.GET.get("sort", "newest")
    sort_map = {"newest": "-created_at", "price_low": "price", "price_high": "-price", "name": "name"}
    products = products.order_by(sort_map.get(sort, "-created_at"))
    page_obj = Paginator(products, 12).get_page(request.GET.get("page", 1))
    return render(request, "catalog.html", {
        "products": page_obj,
        "categories": Category.objects.annotate(product_count=Count("cat")).order_by("name"),
        "active_category": active_category,
        "current_sort": sort,
        "query": query,
    })


def category_products(request, slug):
    return catalog(request, category_slug=slug)


def _absolute_url(request, url):
    if not url:
        return ""
    return request.build_absolute_uri(url)


def _json_for_script(data):
    return (
        json.dumps(data, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def product_detail(request, slug):
    product = get_object_or_404(_store_products(), slug=slug)
    variants = list(product.variants.all())
    all_images = list(product.images.all())

    has_variants = bool(variants)
    all_variants_out_of_stock = has_variants and not any(variant.stock > 0 for variant in variants)
    is_out_of_stock = all_variants_out_of_stock or (not has_variants and product.stock_quantity <= 0)

    # L'image d'une variante est résolue depuis le prefetch déjà en mémoire.
    primary_by_color = {
        image.color_id: image.image.url
        for image in all_images
        if image.is_primary and image.color_id
    }
    fallback_image = next(
        (image.image.url for image in all_images if image.is_primary),
        all_images[0].image.url if all_images else product.imageURL,
    )
    for variant in variants:
        variant.display_image_url = primary_by_color.get(variant.color_id, fallback_image)

    review_probe = list(
        Review.objects.filter(product=product, status="approved")
        .only("id", "name", "rating", "comment", "image", "created_at")
        .order_by("-created_at")[:3]
    )
    initial_reviews = review_probe[:2]
    review_has_more = len(review_probe) > 2
    average_rating_value = product.get_average_rating()
    review_count_value = product.review_count()

    recommendations = _recommended_products([product], limit=8)

    image_urls = [_absolute_url(request, image.image.url) for image in all_images if image.image]
    if not image_urls and product.imageURL:
        image_urls = [_absolute_url(request, product.imageURL)]
    product_url = request.build_absolute_uri(product.get_absolute_url())
    product_schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "description": (product.description_detaillee or product.description or "")[:5000],
        "url": product_url,
        "image": image_urls,
        "offers": {
            "@type": "Offer",
            "priceCurrency": settings.STRIPE_CURRENCY.upper(),
            "price": str(product.price),
            "url": product_url,
            "availability": "https://schema.org/OutOfStock" if is_out_of_stock else "https://schema.org/InStock",
            "itemCondition": "https://schema.org/NewCondition",
        },
    }
    if product.sku:
        product_schema["sku"] = product.sku
    if product.category:
        product_schema["category"] = product.category.name
    if review_count_value:
        product_schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": average_rating_value,
            "reviewCount": review_count_value,
            "bestRating": 5,
            "worstRating": 1,
        }
    if initial_reviews:
        product_schema["review"] = [
            {
                "@type": "Review",
                "author": {"@type": "Person", "name": review.name or "Client"},
                "datePublished": review.created_at.date().isoformat(),
                "reviewBody": review.comment,
                "reviewRating": {"@type": "Rating", "ratingValue": review.rating, "bestRating": 5, "worstRating": 1},
            }
            for review in initial_reviews
        ]

    return render(request, "product_detail.html", {
        "product": product,
        "variants": variants,
        "reviews": initial_reviews,
        "review_has_more": review_has_more,
        "review_form": ReviewForm(),
        "related_products": recommendations,
        "all_images": all_images,
        "is_out_of_stock": is_out_of_stock,
        "all_variants_out_of_stock": all_variants_out_of_stock,
        "average_rating_value": average_rating_value,
        "review_count_value": review_count_value,
        "product_og_image": image_urls[0] if image_urls else "",
        "product_schema_json": _json_for_script(product_schema),
    })


@require_GET
def product_reviews_more(request, slug):
    product = get_object_or_404(Product.objects.only("id", "slug"), slug=slug)
    try:
        offset = max(0, int(request.GET.get("offset", 0)))
    except (TypeError, ValueError):
        offset = 0
    limit = 2
    rows = list(
        Review.objects.filter(product=product, status="approved")
        .only("id", "name", "rating", "comment", "image", "created_at")
        .order_by("-created_at")[offset:offset + limit + 1]
    )
    reviews = rows[:limit]
    html = "".join(
        render_to_string("partials/review_card.html", {"review": review}, request=request)
        for review in reviews
    )
    return JsonResponse({
        "success": True,
        "html": html,
        "count": len(reviews),
        "next_offset": offset + len(reviews),
        "has_more": len(rows) > limit,
    })


def cart(request):
    cart_obj = get_or_create_cart(request)
    if request.method == "POST":
        form = CartForm(request.POST)
        if form.is_valid():
            cart_obj.code_promo = form.cleaned_data["code_promo"].strip().upper()
            cart_obj.save(update_fields=["code_promo"])
            if cart_obj.code_promo in {"MALI10", "ML", "OH", "OVO", "OMG", settings.NEWSLETTER_PROMO_CODE}:
                messages.success(request, "Code promotionnel appliqué.")
            else:
                messages.error(request, "Ce code promotionnel n'est pas valide.")
            return redirect("cart")
    else:
        form = CartForm(initial={"code_promo": cart_obj.code_promo})
    items = list(
        cart_obj.items.select_related(
            "product", "product__category", "variant__color", "variant__size"
        ).prefetch_related(
            Prefetch("product__images", queryset=ProductImage.objects.order_by("order"))
        )
    )
    subtotal_price = sum((item.get_subtotal() for item in items), Decimal("0.00"))
    total_price = cart_obj.get_total(items)
    cart_item_count = cart_obj.get_items_count(items)
    recommendations = _recommended_products([item.product for item in items], limit=8) if items else []
    return render(request, "cart.html", {
        "cart": cart_obj,
        "cart_items": items,
        "subtotal_price": subtotal_price,
        "total_price": total_price,
        "cart_item_count": cart_item_count,
        "form": form,
        "recommended_products": recommendations,
    })


def remove_cart(request):
    get_or_create_cart(request).delete()
    return redirect("cart")


def _resolve_variant(product, variant_id):
    variants = list(product.variants.all())
    if variant_id:
        try:
            wanted_id = int(variant_id)
        except (TypeError, ValueError):
            raise Http404("Variante introuvable")
        variant = next((item for item in variants if item.id == wanted_id), None)
        if variant is None:
            raise Http404("Variante introuvable")
        return variant
    if len(variants) == 1:
        return variants[0]
    return None


@require_POST
def add_to_cart(request, slug):
    try:
        data = json.loads(request.body or "{}")
        quantity = max(1, int(data.get("quantity", 1)))
        product = get_object_or_404(Product.objects.prefetch_related("variants"), slug=slug)
        variant_id = data.get("variante") or data.get("variant_id")
        variant = _resolve_variant(product, variant_id)
        if len(list(product.variants.all())) > 1 and not variant:
            return JsonResponse({"success": False, "message": "Choisissez une variante avant d'ajouter ce produit."}, status=400)
        available = variant.stock if variant else product.stock_quantity
        if available < quantity:
            return JsonResponse({"success": False, "message": f"Stock insuffisant : {available} disponible(s)."}, status=400)

        cart_obj = get_or_create_cart(request)
        with transaction.atomic():
            item, created = CartItem.objects.get_or_create(cart=cart_obj, product=product, variant=variant, defaults={"quantity": quantity})
            if not created:
                if available < item.quantity + quantity:
                    return JsonResponse({"success": False, "message": f"Stock insuffisant : {available} disponible(s)."}, status=400)
                item.quantity += quantity
                item.save(update_fields=["quantity"])
        return JsonResponse({"success": True, "message": f"{product.name} ajouté au panier.", "panier": cart_obj.get_items_count()})
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"success": False, "message": "Quantité invalide."}, status=400)


@require_POST
def update_cart(request):
    try:
        data = json.loads(request.body or "{}")
        cart_obj = get_or_create_cart(request)
        item = get_object_or_404(CartItem.objects.select_related("product", "variant"), id=data.get("item_id"), cart=cart_obj)
        action = data.get("action")
        if action == "increase":
            available = item.variant.stock if item.variant else item.product.stock_quantity
            if item.quantity >= available:
                return JsonResponse({"success": False, "message": "Stock maximum atteint."}, status=400)
            item.quantity += 1; item.save(update_fields=["quantity"])
        elif action == "decrease":
            if item.quantity <= 1:
                item.delete()
            else:
                item.quantity -= 1; item.save(update_fields=["quantity"])
        elif action == "remove":
            item.delete()
        else:
            return JsonResponse({"success": False, "message": "Action invalide."}, status=400)
        return JsonResponse({"success": True, "panier": cart_obj.get_items_count(), "total": float(cart_obj.get_total())})
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Requête invalide."}, status=400)


@require_GET
def cart_summary(request):
    cart_obj = get_or_create_cart(request)
    cart_items = list(
        cart_obj.items.select_related("product", "variant__color", "variant__size").prefetch_related(
            Prefetch("product__images", queryset=ProductImage.objects.order_by("order"))
        )
    )
    items = []
    for item in cart_items:
        image = item.product.first_store_image
        variant_bits = []
        if item.variant and item.variant.color: variant_bits.append(item.variant.color.name)
        if item.variant and item.variant.size: variant_bits.append(item.variant.size.name)
        items.append({
            "id": item.id,
            "name": item.product.name,
            "slug": item.product.slug,
            "image": image.image.url if image else item.product.imageURL,
            "variant": " · ".join(variant_bits),
            "quantity": item.quantity,
            "subtotal": float(item.get_subtotal()),
        })
    return JsonResponse({
        "success": True,
        "count": cart_obj.get_items_count(cart_items),
        "total": float(cart_obj.get_total(cart_items)),
        "items": items,
    })


def _discount_multiplier(code):
    code = (code or "").strip().upper()
    if code == settings.NEWSLETTER_PROMO_CODE:
        return Decimal("0.92")
    if code in {"MALI10", "ML", "OH", "OVO"}:
        return Decimal("0.90")
    if code == "OMG":
        return Decimal("0.50")
    return Decimal("1.00")


def _stripe_unit_amount(price):
    currency = settings.STRIPE_CURRENCY.lower()
    zero_decimal = {"bif", "clp", "djf", "gnf", "jpy", "kmf", "krw", "mga", "pyg", "rwf", "ugx", "vnd", "vuv", "xaf", "xof", "xpf"}
    value = Decimal(price)
    if currency in zero_decimal:
        return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _checkout_lines(request, data):
    source = data.get("source", "cart")
    if source == "buy_now":
        product = get_object_or_404(Product.objects.prefetch_related("variants"), slug=data.get("slug"))
        quantity = max(1, int(data.get("quantity", 1)))
        variant = _resolve_variant(product, data.get("variant_id") or data.get("variante"))
        if len(list(product.variants.all())) > 1 and not variant:
            raise ValueError("Choisissez une variante avant le paiement.")
        available = variant.stock if variant else product.stock_quantity
        if available < quantity:
            raise ValueError("Stock insuffisant pour cette quantité.")
        return source, None, [(product, variant, quantity, product.price)]

    cart_obj = get_or_create_cart(request)
    cart_items = list(cart_obj.items.select_related("product", "variant__color", "variant__size"))
    if not cart_items:
        raise ValueError("Votre panier est vide.")
    multiplier = _discount_multiplier(cart_obj.code_promo)
    lines = [(i.product, i.variant, i.quantity, (i.product.price * multiplier).quantize(Decimal("0.01"))) for i in cart_items]
    return "cart", cart_obj, lines


@require_POST
def create_checkout_session(request):
    if not settings.STRIPE_SECRET_KEY:
        return JsonResponse({"success": False, "message": "Stripe n'est pas encore configuré. Ajoutez STRIPE_SECRET_KEY dans le fichier .env."}, status=503)
    try:
        data = json.loads(request.body or "{}")
        source, cart_obj, lines = _checkout_lines(request, data)
        stripe.api_key = settings.STRIPE_SECRET_KEY
        line_items = []
        for product, variant, quantity, unit_price in lines:
            name = product.name
            variant_text = []
            if variant and variant.color: variant_text.append(variant.color.name)
            if variant and variant.size: variant_text.append(variant.size.name)
            if variant_text: name += " — " + " / ".join(variant_text)
            line_items.append({
                "price_data": {
                    "currency": settings.STRIPE_CURRENCY.lower(),
                    "product_data": {"name": name, "description": (product.description or "")[:300]},
                    "unit_amount": _stripe_unit_amount(unit_price),
                },
                "quantity": quantity,
            })

        payload = {
            "mode": "payment",
            "line_items": line_items,
            "success_url": request.build_absolute_uri(reverse("checkout_success")) + "?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": request.build_absolute_uri(reverse("checkout_cancel")),
            "billing_address_collection": "required",
            "phone_number_collection": {"enabled": True},
            "metadata": {"source": source, "cart_id": str(cart_obj.id) if cart_obj else ""},
        }
        if any(p.product_type == "physical" for p, _, _, _ in lines) and settings.STRIPE_SHIPPING_COUNTRIES:
            payload["shipping_address_collection"] = {"allowed_countries": settings.STRIPE_SHIPPING_COUNTRIES}

        session = stripe.checkout.Session.create(**payload)
        total = sum(Decimal(unit) * qty for _, _, qty, unit in lines)
        payment = PaymentRecord.objects.create(
            stripe_session_id=session.id,
            cart_id=cart_obj.id if cart_obj else None,
            amount_total=total,
            currency=settings.STRIPE_CURRENCY.upper(),
            status="pending",
        )
        SaleItem.objects.bulk_create([
            SaleItem(
                payment=payment,
                product_id=product.id,
                product_name=product.name,
                variant_id=variant.id if variant else None,
                quantity=quantity,
                unit_price=unit_price,
            )
            for product, variant, quantity, unit_price in lines
        ])
        return JsonResponse({"success": True, "url": session.url})
    except ValueError as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=400)
    except stripe.StripeError as exc:
        return JsonResponse({"success": False, "message": getattr(exc, "user_message", None) or "Stripe a refusé la création du paiement."}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Requête invalide."}, status=400)


def _send_payment_receipt(payment_id):
    """Envoie un reçu HTML idempotent via le backend e-mail Django (Gmail SMTP en prod)."""
    if not getattr(settings, "SEND_ORDER_RECEIPTS", True):
        return False

    with transaction.atomic():
        payment = (
            PaymentRecord.objects.select_for_update()
            .prefetch_related("items")
            .filter(id=payment_id)
            .first()
        )
        if not payment or payment.status != "paid":
            return False
        if payment.receipt_sent_at:
            return True
        if not payment.customer_email:
            payment.receipt_error = "Adresse e-mail client absente du paiement Stripe."
            payment.save(update_fields=["receipt_error", "updated_at"])
            return False

        items = list(payment.items.all())
        context = {
            "payment": payment,
            "items": items,
            "store_name": settings.STORE_NAME,
            "store_currency_symbol": settings.STORE_CURRENCY_SYMBOL,
            "support_email": getattr(settings, "SUPPORT_EMAIL", settings.DEFAULT_FROM_EMAIL),
        }
        html_message = render_to_string("emails/order_receipt.html", context)
        text_message = strip_tags(html_message)
        try:
            sent = send_mail(
                subject=f"Votre reçu {settings.STORE_NAME}",
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[payment.customer_email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as exc:
            payment.receipt_error = str(exc)[:1000]
            payment.save(update_fields=["receipt_error", "updated_at"])
            logger.exception("Échec d'envoi du reçu de paiement %s", payment.id)
            return False

        if sent:
            payment.receipt_sent_at = timezone.now()
            payment.receipt_error = ""
            payment.save(update_fields=["receipt_sent_at", "receipt_error", "updated_at"])
            return True
        payment.receipt_error = "Le backend e-mail n'a confirmé aucun envoi."
        payment.save(update_fields=["receipt_error", "updated_at"])
        return False


def _finalize_payment(session):
    session_id = session.get("id") if isinstance(session, dict) else session.id
    payment_status = session.get("payment_status") if isinstance(session, dict) else session.payment_status
    customer_details = session.get("customer_details", {}) if isinstance(session, dict) else getattr(session, "customer_details", None)
    if payment_status != "paid":
        return None
    with transaction.atomic():
        payment = PaymentRecord.objects.select_for_update().filter(stripe_session_id=session_id).first()
        if not payment:
            return None
        payment.status = "paid"
        if customer_details:
            payment.customer_email = customer_details.get("email", "") if isinstance(customer_details, dict) else getattr(customer_details, "email", "") or ""

        if not payment.inventory_applied:
            lines = list(payment.items.all())
            product_ids = {line.product_id for line in lines}
            products = {
                product.id: product
                for product in Product.objects.select_for_update().filter(id__in=product_ids)
            }

            variant_product_ids = {
                line.product_id for line in lines if line.variant_id and line.product_id in products
            }
            all_variants = list(
                ProductVariant.objects.select_for_update().filter(product_id__in=variant_product_ids)
            )
            variants_by_id = {variant.id: variant for variant in all_variants}
            variants_by_product = {}
            for variant in all_variants:
                variants_by_product.setdefault(variant.product_id, []).append(variant)

            changed_variant_ids = set()
            changed_product_ids = set()
            for line in lines:
                product = products.get(line.product_id)
                if not product:
                    continue
                if line.variant_id:
                    variant = variants_by_id.get(line.variant_id)
                    if variant and variant.product_id == product.id:
                        variant.stock = max(0, variant.stock - line.quantity)
                        changed_variant_ids.add(variant.id)
                        changed_product_ids.add(product.id)
                else:
                    product.stock_quantity = max(0, product.stock_quantity - line.quantity)
                    changed_product_ids.add(product.id)

            if changed_variant_ids:
                ProductVariant.objects.bulk_update(
                    [variants_by_id[variant_id] for variant_id in changed_variant_ids],
                    ["stock"],
                )

            products_to_update = []
            for product_id in changed_product_ids:
                product = products[product_id]
                if product_id in variant_product_ids:
                    product.stock_quantity = sum(
                        variant.stock for variant in variants_by_product.get(product_id, [])
                    )
                if product.stock_quantity == 0:
                    product.stock_status = "out_of_stock"
                elif product.stock_quantity < 10:
                    product.stock_status = "low_stock"
                else:
                    product.stock_status = "in_stock"
                products_to_update.append(product)

            if products_to_update:
                Product.objects.bulk_update(products_to_update, ["stock_quantity", "stock_status"])

            payment.inventory_applied = True

        payment.save(update_fields=["status", "customer_email", "inventory_applied"])
        if payment.cart_id:
            Cart.objects.filter(id=payment.cart_id).delete()
        payment_id = payment.id

    _send_payment_receipt(payment_id)
    payment.refresh_from_db(fields=["receipt_sent_at", "receipt_error", "customer_email", "status"])
    return payment


def checkout_success(request):
    session_id = request.GET.get("session_id", "")
    payment = None
    stripe_error = None
    if session_id and settings.STRIPE_SECRET_KEY:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.retrieve(session_id)
            payment = _finalize_payment(session)
            if not payment:
                payment = PaymentRecord.objects.filter(stripe_session_id=session_id).first()
        except stripe.StripeError:
            stripe_error = "Impossible de vérifier le paiement pour le moment."
    return render(request, "checkout_success.html", {"payment": payment, "stripe_error": stripe_error})


def checkout_cancel(request):
    return render(request, "checkout_cancel.html")


@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponse(status=204)
    try:
        event = stripe.Webhook.construct_event(request.body, request.META.get("HTTP_STRIPE_SIGNATURE", ""), settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponse(status=400)
    if event["type"] in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
        _finalize_payment(event["data"]["object"])
    return HttpResponse(status=200)


def contact(request):
    return render(request, "contact.html", {"form": ContactForm(), "user_name": request.user.username if request.user.is_authenticated else ""})


@require_POST
def contact_form_save(request):
    form = ContactForm(request.POST, request.FILES)
    if form.is_valid():
        if not request.session.session_key: request.session.create()
        contact_obj = form.save(commit=False)
        contact_obj.session_key = request.session.session_key
        contact_obj.username = request.user.username if request.user.is_authenticated else None
        contact_obj.save()
        return JsonResponse({"success": True, "redirect_url": reverse("contact"), "message": "Votre message a bien été envoyé."})
    return JsonResponse({"success": False, "message": "Formulaire invalide.", "errors": form.errors}, status=400)


@require_GET
def search_view(request):
    query = request.GET.get("q", "").strip()[:200]
    if len(query) < 2:
        products = Product.objects.none()
    else:
        safe_query = escape(query)
        products = _store_products().filter(
            Q(name__icontains=safe_query) | Q(description__icontains=safe_query) |
            Q(description_detaillee__icontains=safe_query) | Q(category__name__icontains=safe_query)
        ).order_by("name")
    page_obj = Paginator(products, 20).get_page(request.GET.get("page", 1)) if query else []
    total_results = page_obj.paginator.count if query else 0
    return render(request, "search.html", {"query": query, "products": page_obj, "total_results": total_results})


@require_GET
def search_autocomplete(request):
    query = request.GET.get("q", "").strip()[:100]
    if len(query) < 2: return JsonResponse({"results": []})
    products = _store_products().filter(Q(name__icontains=query) | Q(description_detaillee__icontains=query))[:8]
    results = []
    for p in products:
        image = p.first_store_image
        results.append({"name": p.name, "slug": p.slug, "price": float(p.price), "image": image.image.url if image else p.imageURL})
    return JsonResponse({"results": results})


@require_POST
def newsletter_subscribe(request):
    try:
        if request.content_type == "application/json":
            payload = json.loads(request.body or "{}")
            email = (payload.get("email") or "").strip().lower()
        else:
            email = (request.POST.get("email") or "").strip().lower()
        validate_email(email)
    except (ValidationError, json.JSONDecodeError, TypeError):
        return JsonResponse({"success": False, "message": "Saisissez une adresse e-mail valide."}, status=400)

    subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
    if not subscriber.is_active:
        subscriber.is_active = True
        subscriber.save(update_fields=["is_active"])

    request.session["newsletter_subscribed"] = True
    message = "Bienvenue ! Votre remise de 8 % est prête." if created else "Vous êtes déjà inscrit(e). Votre remise de 8 % reste disponible."
    return JsonResponse({
        "success": True,
        "message": message,
        "promo_code": settings.NEWSLETTER_PROMO_CODE,
        "discount": 8,
    })


@require_POST
def submit_review(request):
    product = get_object_or_404(Product, slug=request.POST.get("product_slug"))
    form = ReviewForm(request.POST, request.FILES)
    if form.is_valid():
        review = form.save(commit=False); review.product = product; review.save()
        return JsonResponse({"success": True, "message": "Merci ! Votre avis sera affiché après validation.", "redirect_url": product.get_absolute_url()})
    return JsonResponse({"success": False, "message": "Formulaire invalide.", "errors": form.errors}, status=400)


def tout_les_messages(request):
    return render(request, "messages.html", {"contacts": Contact.objects.order_by("-added_at")})


def supprimer_message(request):
    if request.session.session_key:
        Contact.objects.filter(session_key=request.session.session_key).delete()
    return redirect("tout_les_messages")
