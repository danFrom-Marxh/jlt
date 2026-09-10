from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, F, Sum
from django.core.exceptions import ValidationError
import uuid

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    STOCK_STATUS = [
        ('in_stock', 'En Stock'),
        ('low_stock', 'Stock Limité'),
        ('out_of_stock', 'Rupture de Stock'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True , related_name="cat")
    price = models.DecimalField(decimal_places=2, max_digits=7)
    description = models.TextField()
    image = models.ImageField()
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    stock_status = models.CharField(max_length=20, choices=STOCK_STATUS, default='in_stock')
    old_price = models.DecimalField(decimal_places=2, max_digits=7, blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    taille = models.CharField(max_length=200, blank=True, null=True)
    description_detaillee = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=100, unique=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True, null=True)
    PRODUCT_TYPE_CHOICES = [
        ('physical', 'Physique'),
        ('digital', 'Numérique'),
    ]
    
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='physical')

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        
        # Mise à jour automatique du statut de stock
        if self.stock_quantity == 0:
            self.stock_status = 'out_of_stock'
        elif self.stock_quantity < 10:
            self.stock_status = 'low_stock'
        else:
            self.stock_status = 'in_stock'
            
            
        super().save(*args, **kwargs)

    @property
    def est_recent(self):
        return bool(self.created_at and self.created_at >= timezone.now() - timedelta(days=7))
    
    def get_discount_percentage(self):
        if self.old_price and self.old_price > self.price:
            return int(((self.old_price - self.price) / self.old_price) * 100)
        return 0
    
    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url
    
    def average_rating(self):
        return self.get_average_rating()

    def get_average_rating(self):
        # Les vitrines annotent cette valeur via des sous-requêtes corrélées :
        # aucun chargement de tous les avis et aucune requête N+1 par carte.
        if hasattr(self, "store_average_rating"):
            annotated = self.store_average_rating
            return round(float(annotated), 1) if annotated is not None else 0

        prefetched = getattr(self, "approved_reviews", None)
        if prefetched is not None:
            if not prefetched:
                return 0
            return round(sum(review.rating for review in prefetched) / len(prefetched), 1)

        approved_reviews = self.reviews.filter(status='approved')
        value = approved_reviews.aggregate(models.Avg('rating'))['rating__avg']
        return round(value, 1) if value is not None else 0
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('product_detail', kwargs={'slug': self.slug})

    def review_count(self):
        if hasattr(self, "store_review_count"):
            return int(self.store_review_count or 0)
        prefetched = getattr(self, "approved_reviews", None)
        if prefetched is not None:
            return len(prefetched)
        return self.reviews.filter(status="approved").count()

    @property
    def first_store_image(self):
        cached = getattr(self, "_prefetched_objects_cache", {}).get("images")
        if cached is not None:
            return cached[0] if cached else None
        return self.images.order_by("order").first()

    @property
    def variants_count(self):
        cached = getattr(self, "_prefetched_objects_cache", {}).get("variants")
        if cached is not None:
            return len(cached)
        return self.variants.count()

    @property
    def first_variant_id(self):
        cached = getattr(self, "_prefetched_objects_cache", {}).get("variants")
        if cached is not None:
            return cached[0].id if cached else ""
        first = self.variants.order_by("id").first()
        return first.id if first else ""
    
    def __str__(self):
        return self.name
    
    @property
    def total_stock(self):
        cached = getattr(self, "_prefetched_objects_cache", {}).get("variants")
        variants = cached if cached is not None else self.variants.all()
        return sum(v.stock for v in variants)

    @property
    def store_out_of_stock(self):
        """État boutique sans requête supplémentaire quand les variantes sont préchargées."""
        cached = getattr(self, "_prefetched_objects_cache", {}).get("variants")
        if cached:
            return not any(variant.stock > 0 for variant in cached)
        return self.stock_quantity <= 0
    
    def images_by_color(self, color):
        return self.images.filter(color=color).order_by('order')


class Color(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    code_hex = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"couleur {self.name}"


class Size(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    def __str__(self):
        return f"Taille {self.name}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name='color_images', null=True, blank=True)
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        constraints = [
            # Une seule image principale par produit + couleur
            models.UniqueConstraint(
                fields=['product', 'color'],
                condition=models.Q(is_primary=True),
                name='unique_primary_per_color'
            )
        ]

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Décocher l'ancienne image principale pour cette couleur
            ProductImage.objects.filter(
                product=self.product,
                color=self.color,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        color_name = self.color.name if self.color else "Aucune couleur"
        return f"{self.product.name} | {color_name} | {'Principal' if self.is_primary else 'Secondaire'}"

    
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants",)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, related_name="product_variants",)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True, related_name="product_variants",)
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=100, blank=True, null=True, unique=True)

    class Meta:
        constraints= [
            models.CheckConstraint(
                condition=Q(stock__gte=0),
                name="variants_stock_gte_0",),
        ]
    def clean(self):
        qs = ProductVariant.objects.filter(product=self.product, color=self.color, size=self.size,)
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            raise ValidationError("Cette combinaison produit/taille/couleur existe déjà")
    
    def __str__(self):
        parts = [self.product.name]
        if self.color:
            parts.append(f"Couleur: {self.color}")
        if self.size:
            parts.append(f"Taille: {self.size}")
        if not self.color and not self.size:
            parts.append("sans variante")
        return " - ".join(parts)

    @property
    def primary_image(self):
        # Utilise les images préchargées du produit quand elles existent.
        product = self.product
        cached = getattr(product, "_prefetched_objects_cache", {}).get("images")
        if cached is not None:
            if self.color_id:
                image = next((img for img in cached if img.color_id == self.color_id and img.is_primary), None)
                if image:
                    return image.image.url
            image = next((img for img in cached if img.is_primary), None)
            if image:
                return image.image.url
            if cached:
                return cached[0].image.url
            return product.imageURL

        if self.color_id:
            img = product.images.filter(color_id=self.color_id, is_primary=True).first()
            if img:
                return img.image.url
        img = product.images.filter(is_primary=True).first()
        if img:
            return img.image.url
        return product.imageURL

    
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    code_promo = models.CharField(max_length=100)
    
    def get_total(self, items=None):
        if items is None:
            cached = getattr(self, "_prefetched_objects_cache", {}).get("items")
            items = cached if cached is not None else list(self.items.select_related("product"))
        subtotal = sum((item.get_subtotal() for item in items), 0)
        code = (self.code_promo or "").strip().upper()
        if code == getattr(settings, "NEWSLETTER_PROMO_CODE", "JLT8"):
            return subtotal - (subtotal * 8) / 100
        if code in ["MALI10", "ML", "OH", "OVO"]:
            return subtotal - (subtotal * 10) / 100
        if code == "OMG":
            return subtotal - (subtotal * 50) / 100
        return subtotal

    def get_items_count(self, items=None):
        if items is not None:
            return sum(item.quantity for item in items)
        cached = getattr(self, "_prefetched_objects_cache", {}).get("items")
        if cached is not None:
            return sum(item.quantity for item in cached)
        return self.items.aggregate(total=Sum("quantity"))["total"] or 0

    def __str__(self):
        owner = self.user.username if self.user else f"Session: {self.session_key}"
        return f"Panier de {owner}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="cart_items", null=True)
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "variant"],
                name="unique_variant_per_cart"
            )
        ]

    def get_subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.variant}"


class Contact(models.Model):
    session_key = models.CharField(max_length=100, blank=True, null=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100)
    phone_number = models.CharField(null=True, blank=True)
    message = models.TextField()
    profil = models.ImageField(null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class meta:
        ordering = ['-order']

    def __str__(self):
        if self.username:
            return f"message de {self.username}"
        else:
            if self.first_name:
                return f"message de {self.first_name}"
            elif self.last_name:
                return f"message de {self.last_name}"
        
        return f"message de {self.email}"
    


class Review(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    name = models.CharField(max_length=100, default="Invité")
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    image = models.ImageField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        name = self.name
        return f"{name} - {self.product.name} ({self.rating}⭐)"


class PaymentRecord(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('paid', 'Payé'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
    ]
    stripe_session_id = models.CharField(max_length=255, unique=True)
    cart_id = models.PositiveIntegerField(null=True, blank=True)
    amount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default='EUR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    customer_email = models.EmailField(blank=True)
    inventory_applied = models.BooleanField(default=False)
    receipt_sent_at = models.DateTimeField(null=True, blank=True)
    receipt_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.stripe_session_id} - {self.status}"


class SaleItem(models.Model):
    payment = models.ForeignKey(PaymentRecord, on_delete=models.CASCADE, related_name='items')
    product_id = models.UUIDField()
    product_name = models.CharField(max_length=200)
    variant_id = models.PositiveIntegerField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} × {self.product_name}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email
