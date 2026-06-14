from django.contrib import admin
from .models import *
from django.utils.html import format_html

# Register your models here.


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    list_display = [
        'product_name_display',
        'category',
        'stock_display',
        # 'rating_display',
        'created_at'
    ]

    def stock_display(self, obj):
        """Affiche le stock avec code couleur"""
        if obj.stock_quantity == 0:
            return format_html(
                '<span style="background: #e74c3c; color: white; padding: 5px 12px; '
                'border-radius: 12px; font-weight: 600;">{}</span>',
                'Rupture'  # ✅
            )
        elif obj.stock_quantity < 10:
            return format_html(
                '<span style="background: #f39c12; color: white; padding: 5px 12px; '
                'border-radius: 12px; font-weight: 600;">{} unités</span>',
                obj.stock_quantity
            )
        else:
            return format_html(
                '<span style="background: #27ae60; color: white; padding: 5px 12px; '
                'border-radius: 12px; font-weight: 600;">{} unités</span>',
                obj.stock_quantity
            )
    stock_display.short_description = 'Stock'

    def product_name_display(self, obj):
        """Affiche le nom avec une image miniature si disponible"""
        image = obj.images.filter(is_primary=True).first()
        if not image:
            image = obj.images.first()
        
        if image:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 10px;">'
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; '
                'border-radius: 6px; border: 2px solid #ddd;"/>'
                '<strong>{}</strong>'
                '</div>',
                image.image.url,
                obj.name
            )
        return format_html('<strong>{}</strong>', obj.name)
    product_name_display.short_description = 'Produit'

admin.site.register(Contact)
admin.site.register(ProductImage)
admin.site.register(Category)
admin.site.register(Color)
admin.site.register(Review)
admin.site.register(Size)
admin.site.register(ProductVariant)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_owner', 'get_items_count', 'get_total', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_owner(self, obj):
        return obj.user.username if obj.user else f"Session: {obj.session_key}"
    get_owner.short_description = 'Propriétaire'
    
    def get_items_count(self, obj):
        return obj.get_items_count()
    get_items_count.short_description = "Nombre d'articles"
    
    def get_total(self, obj):
        return f"{obj.get_total()} FCFA"
    get_total.short_description = 'Total'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'variant', 'quantity', 'get_subtotal']
    list_filter = ['cart__created_at']
    search_fields = ['product__name']
    
    def get_subtotal(self, obj):
        return f"{obj.get_subtotal()} FCFA"
    get_subtotal.short_description = 'Sous-total'