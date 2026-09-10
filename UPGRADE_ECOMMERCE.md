# Mise à niveau e-commerce

## Fonctionnalités principales

- Accueil e-commerce entièrement redesigné.
- Sections : nouveautés, plus appréciés, plus demandés / plus achetés, coups de cœur.
- Catalogue global et pages par catégories.
- Fiche produit avec variantes, galerie, stock, quantité, avis, ajout panier et achat immédiat.
- Mini-panier coulissant global depuis la droite.
- Panier complet AJAX.
- Stripe Checkout côté serveur.
- Webhook Stripe idempotent grâce à `PaymentRecord.inventory_applied`.
- Enregistrement des lignes vendues dans `SaleItem`.
- Décrémentation de stock après paiement confirmé.
- Recherche et autocomplétion modernisées.
- Pages succès / annulation de paiement.

## À faire avant de passer en production

1. Copier `.env.example` vers `.env`.
2. Ajouter les vraies clés Stripe.
3. Exécuter `python manage.py migrate`.
4. Configurer le webhook public `/api/stripe/webhook/` dans Stripe.
5. Vérifier la devise (`STRIPE_CURRENCY`) et le symbole (`STORE_CURRENCY_SYMBOL`).
6. Mettre `DEBUG=False`, définir `ALLOWED_HOSTS` et une `SECRET_KEY` forte.
7. Configurer un stockage persistant pour les médias produits.

La base SQLite fournie a également été mise à niveau avec les tables de paiement afin de conserver les données existantes et de permettre une reprise immédiate du projet.
