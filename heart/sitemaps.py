from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Category, Product


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return ["home", "catalog", "services", "apropos", "contact"]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == "home" else (0.9 if item == "catalog" else 0.5)


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.only("slug", "created_at").order_by("-created_at")

    def lastmod(self, obj):
        return obj.created_at


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.only("slug").order_by("name")

    def location(self, obj):
        return reverse("category_products", kwargs={"slug": obj.slug})
