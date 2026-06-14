from .models import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import urllib.parse
import json
from .forms import *
from django.conf import settings
import requests
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Avg, Count, F, Prefetch
from django.db import transaction
from django.utils.html import escape
from django.http import JsonResponse
from django.urls import reverse
# import stripe
from decimal import Decimal
import json
from django.template import Context
from django.views.generic import View

API_KEY = settings.OPENWEATHERMAP_API_KEY
GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

@require_GET
def search_city(request):
    query = request.GET.get("q", "").strip()

    if not query:

        return JsonResponse({"results": []})

    try:
        response = requests.get(
            GEOCODING_URL,
            params={
                "q": query,
                "limit": 5,
                "appid": API_KEY,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data:
            results.append({
                "name": item.get("name"),
                "country": item.get("country"),
                "state": item.get("state", ""),
                "lat": item.get("lat"),
                "lon": item.get("lon"),
            })

        return JsonResponse({"results": results})

    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def city_weather(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    if not lat or not lon:
        return JsonResponse({"error": "Paramètres lat et lon requis."}, status=400)

    try:
        weather_response = requests.get(
            WEATHER_URL,
            params={
                "lat": lat,
                "lon": lon,
                "appid": API_KEY,
                "units": "metric",
                "lang": "fr",
            },
            timeout=10,
        )
        weather_response.raise_for_status()
        current_data = weather_response.json()

        forecast_response = requests.get(
            FORECAST_URL,
            params={
                "lat": lat,
                "lon": lon,
                "appid": API_KEY,
                "units": "metric",
                "lang": "fr",
            },
            timeout=10,
        )
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        return JsonResponse({
            "current": current_data,
            "forecast": forecast_data,
        })

    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_or_create_cart(request):
    try:
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
            print(f"utilisateur connecté et panier récupéré {cart}")
        else:
            print("deuxième cas")
            if request.session.session_key is None:
                request.session['init'] = True
                request.session.save()
                print(f" cas 1 Votre clé de session est : {request.session.session_key}")
            cart, created = Cart.objects.get_or_create(session_key=request.session.session_key, user=None)
            print(f"utilisateur non connecté et panier récupéré {cart}")
        return cart
    except Exception as e:
        print(f"problème de panier {str(e)}")
    return None


def home(request):
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product')
    sort_by = request.GET.get('sort', 'name')
    categories_dispo = Category.objects.all()
    reviews = Review.objects.filter(status="approved")

    valid_sorts = {
            'price_low': 'price',
            'price_high': '-price',
            'name': 'name',
        }

    valid_categories = []
    for cat in Category.objects.all():
        valid_categories.append(cat.slug)
    print(f"toutes les catégories sont : {valid_categories}")
    if sort_by in valid_sorts:
        products = Product.objects.order_by(valid_sorts[sort_by]).select_related('category').prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.filter(is_primary=True))
        )
        print(f"sort_by est bien dans valid_sorts {sort_by}")
    else:
        if sort_by:
            if sort_by in valid_categories:
                products = Product.objects.filter(category__slug=sort_by).select_related('category').prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.filter(is_primary=True))
        )
                print(f"sort_by est bien dans valid_categories {sort_by}")
        else:
            products = Product.objects.order_by("created_at").select_related('category').prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.filter(is_primary=True)))
    featured_products = Product.objects.filter(is_featured=True)

    page_number = request.GET.get('page', 1)

    paginator = Paginator(products, 4)
    products_page = paginator.get_page(page_number)
    current_page = products_page.number
    total_pages = paginator.num_pages

    if total_pages == 2:
        page_numbers = [1, 2]
    elif total_pages <= 5:
        page_numbers = list(range(1, total_pages + 1))
    elif current_page <= 3:
        page_numbers = [1, 2, 3, 4, '...']
    elif current_page >= total_pages - 3 and total_pages > 9:
        page_numbers = [1, '...',total_pages - 4,total_pages - 3,total_pages - 2, total_pages - 1, total_pages]
    elif current_page + 2 < total_pages and current_page - 2 > 2:
        page_numbers = [1, '...', current_page - 1, current_page, current_page + 1, '...']
    elif current_page + 2 < total_pages and current_page - 2 > 2 and total_pages - current_page <= 3:
        page_numbers = [1, '...', current_page - 1, current_page, current_page + 1, current_page + 2, current_page +3]

    elif current_page + 2 < total_pages:
        page_numbers = [1, current_page - 2, current_page - 1, current_page, current_page + 1, '...']
    elif current_page == total_pages:
        page_numbers = [1, '...', current_page - 2, current_page - 1, current_page]
    elif current_page - 2 > 2 and current_page + 1 == total_pages:
        page_numbers = [1, '...', current_page - 1, current_page, current_page + 1]
    elif current_page - 2 > 2 and current_page + 2 == total_pages:
        page_numbers = [1, '...', current_page - 1, current_page, current_page + 1, total_pages]
    else:
        page_numbers = [1, current_page - 2, current_page - 1, current_page, current_page + 1, current_page + 2] #, '...' total_pages(last element of the list)
    
    left_pages = total_pages - current_page
    real_tot_page = total_pages + 1

    query_params = request.GET.copy()
    print(f"query_params : {query_params}")
    query_params.pop('page', None)
    ctx = {'reviews': reviews, 'page_numbers': page_numbers, 'real_tot_page': real_tot_page, 'left_pages': left_pages, 'current_page': current_page, 'query_params': query_params.urlencode(), 'products': products_page, 'cart_items_count': cart.get_items_count(), 'featured_products':featured_products, 'cart': cart, 'get_total': cart.get_total(), 'cart_items':cart_items, 'current_sort': sort_by, 'categories': categories_dispo, "total_pages": total_pages}

    return render(request, 'home.html', ctx)


def remove_cart(request):
    cart = get_or_create_cart(request)
    cart.delete()
    return redirect('cart')


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related("variants__color", "variants__size", "images", "reviews"), 
        slug=slug
    )
    print(f"documentation de product: {product.__doc__}")
    variants = product.variants.all()
    colors = list({v.color for v in variants if v.color})
    sizes = list({v.size for v in variants if v.size})

    form = AddtoCartForm(slug=slug)
    review_form = ReviewForm()
    reviews = product.reviews.filter(status='approved')

    rating_counts = {i: reviews.filter(rating=i).count() for i in range(1, 6)}
    all_images = product.images.order_by('order')
    # all_images = product.images.select_related('product').order_by('order')
    cart = get_or_create_cart(request)

    context = {
        "product": product,
        "variants": variants,
        "colors": colors,
        "sizes": sizes,
        "form": form,
        "review_form": review_form,
        "reviews": reviews,
        "rating_counts": rating_counts,
        "all_images": all_images,
        "cart": cart,
        "cart_items_count": cart.get_items_count(),
        "DEBUG": settings.DEBUG
    }
    return render(request, 'product_detail.html', context)


def product_reviews(request, product_slug):
    product = Product.objects.get(slug=product_slug)
    reviews = product.reviews.all()

    # Pagination
    paginator = Paginator(reviews, 5)  # Afficher 5 avis par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.is_ajax():
        # Retourner les avis au format JSON
        reviews_data = []
        for review in page_obj.object_list:
            reviews_data.append({
                'author': review.user.username,
                'date': review.created_at.strftime('%d %b %Y'),
                'rating': review.rating,
                'comment': review.comment,
                'image_url': review.image.url if review.image else None,
            })

        return JsonResponse({
            'reviews': reviews_data,
            'has_next': page_obj.has_next(),
        })

    # Rendu initial
    return render(request, 'product_detail.html', {'product': product, 'reviews': page_obj})



def cart(request):
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product', 'variant__color', 'variant__size')
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'cart_items_count': cart.get_items_count(),
        'total_price': cart.get_total()
    }
    return render(request, 'cart.html', context)

class CartView(View):
    "hello"


@require_POST
def add_to_cart(request, slug):
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 0))
        variant_id = data.get('variante')

        product = get_object_or_404(Product, slug=slug)
        variant = ProductVariant.objects.filter(id=variant_id).first() if variant_id else None

        if variant and variant.stock < quantity:
            return JsonResponse({'success': False, 'message': f'Stock insuffisant: {variant.stock} restant.'})
        
        elif int(quantity) <= 0:
            print(f"Ajouter à partir de 1 ")
            return JsonResponse({
                'success': False,
                'message': "Impossible d'ajouter moins de 1 produit ",
            })

        cart = get_or_create_cart(request)
        with transaction.atomic():
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, product=product, variant=variant, defaults={'quantity': quantity}
            )
            if not created:
                if variant and variant.stock < cart_item.quantity + quantity:
                    return JsonResponse({'success': False, 'message': f'Stock insuffisant: {variant.stock} restant.'})
                cart_item.quantity += quantity
                cart_item.save()

        return JsonResponse({
            'success': True,
            'message': f'{product.name} ajouté au panier.',
            'panier': cart.get_items_count()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Erreur serveur.'}, status=500)


@require_POST
def update_cart(request):
    try:
        data = json.loads(request.body)
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=data.get('item_id'), cart=cart)
        action = data.get('action')
        if action == 'increase':
            if cart_item.variant and cart_item.variant.stock <= cart_item.quantity:
                return JsonResponse({'success': False, 'message': f'Stock insuffisant: {cart_item.variant.stock} restant!', "panier": cart.get_items_count()})
            cart_item.quantity += 1
            cart_item.save()
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                item = cart_item.variant.product.name
                cart_item.delete()
                return JsonResponse({'success': True, 'message': 'Produit supprimé.', 'item': item, 'item_deleted': True, 'panier': cart.get_items_count()})

        return JsonResponse({
            'success': True,
            'item_count': cart_item.quantity if cart_item.id else 0,
            'item_prix_total': cart_item.get_subtotal() if cart_item.id else 0,
            'prix_total': cart.get_total(),
            'panier': cart.get_items_count(),
            'item_id': cart_item.id
        })
    except Exception:
        return JsonResponse({'success': False, 'message': 'Erreur serveur.'}, status=500)


def contact(request):
    cart = get_or_create_cart(request)
    form = ContactForm()
    return render(request, 'contact.html', {'form': form, 'cart_items_count': cart.get_items_count(),})


def contact_form_save(request): 
    url = reverse("contact")
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            print(f"formulaire : {form.name}")
            message = form.save(commit=False)
            message.save()
            return JsonResponse({
                "success": True,
                "redirect_url": redirect("contact"),
                "message": "Votre message a été envoyé avec succès! Nous nous éfforcerons à vous répondre dans de bref délai"
            })
        else:
            print(f"formulaire : {form}j;_ç")
            return JsonResponse({
                "success": False,
                "redirect_url": url,
                "message": "erreur lors de l'nregistrement du message"
            })
    else:
        form = ContactForm()

    if form.is_valid():
        message = form.save(commit=False)
        message.save()

    return JsonResponse({
            "success": True,
            "redirect_url": redirect("contact"),
            "message": "Votre message a été envoyé avec succès! Nous nous éfforcerons à vous répondre dans de bref délai"
            })


@require_GET
def search_view(request):
    """
    Vue de recherche sécurisée
    """
    try:
        query = request.GET.get('q', '').strip()
        
        # Limiter la longueur de la recherche
        if len(query) > 200:
            query = query[:200]
        
        products = []
        
        if len(query) >= 2:  # Minimum 2 caractères
            # Échapper les caractères spéciaux
            safe_query = escape(query)
            
            products = Product.objects.filter(
                Q(name__icontains=safe_query) |
                Q(description__icontains=safe_query) |
                Q(description_detaillee__icontains=safe_query) |
                Q(category__name__icontains=safe_query),
                #is_active=True#
            ).select_related('category').prefetch_related(
                Prefetch('images', queryset=ProductImage.objects.filter(is_primary=True))
            ).order_by('name')
            
            # Pagination
            paginator = Paginator(products, 20)
            page_number = request.GET.get('page', 1)
            
            try:
                products_page = paginator.page(page_number)
            except (EmptyPage, PageNotAnInteger):
                products_page = paginator.page(1)
        else:
            products_page = []
        
        context = {
            'query': safe_query if len(query) >= 2 else '',
            'products': products_page,
            'total_results': products.count() if products else 0,
        }   
        return render(request, 'search.html', context)
    
    except Exception as e:
        messages.error(request, f"Erreur recherche: {str(e)}")
        messages.error(request, "Une erreur s'est produite lors de la recherche.")
        return render(request, 'search.html')
    

@require_GET
def search_autocomplete(request):
    """
    Autocomplétion de recherche (sécurisée)
    """
    try:
        query = request.GET.get('q', '').strip()
        
        # Limiter la longueur
        if len(query) > 100:
            query = query[:100]
        
        if len(query) < 2:
            return JsonResponse({'results': []})
        
        # Échapper la requête
        safe_query = escape(query)
        
        products = Product.objects.filter(
            Q(name__icontains=safe_query) | 
            Q(description_detaillee__icontains=safe_query),

            #is_active=True#
        ).select_related('category').prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.filter(is_primary=True))
        )[:10]
        
        results = []
        for p in products:
            image = p.images.first()
            results.append({
                'name': p.name,
                'slug': p.slug,
                'price': float(p.price),
                'old_price': float(p.old_price) if p.old_price else None,
                'image': image.image.url if image else None,
                # 'category': p.category.name
            })
        
        return JsonResponse({'results': results})
    
    except Exception as e:
        messages.error(f"Erreur autocomplete: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Une erreur s\'est produite'
        }, status=500)


@require_POST
def submit_review(request):
    print("submit_review appelée")

    product_slug = request.POST.get("product_slug")
    print("product_slug =", product_slug)

    if not product_slug:
        return JsonResponse({
            "success": False,
            "message": "Slug produit manquant."
        }, status=400)

    product = get_object_or_404(Product, slug=product_slug)

    form = ReviewForm(request.POST, request.FILES)

    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.save()
        messages.success(request, "merci pour votre commentaire nous allons le lire et l'approuver avant de l'afficher")

        return JsonResponse({
            "success": True,
            "message": "Merci pour votre avis !",
            "redirect_url": reverse("product_detail", kwargs={"slug": product_slug})
        })

    print("Erreurs formulaire :", form.errors)

    return JsonResponse({
        "success": False,
        "message": "Formulaire invalide.",
        "errors": form.errors
    }, status=400)
