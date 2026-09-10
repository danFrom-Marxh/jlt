# Just Like That — e-commerce Django

Cette version transforme le projet JLT en boutique e-commerce complète tout en conservant les produits, variantes, avis, contacts et paniers déjà présents dans le projet.

## Ce qui a été ajouté / amélioré

- nouvelle page d'accueil e-commerce avec nouveautés, produits les plus appréciés, produits les plus demandés/achetés et coups de cœur ;
- catalogue séparé avec tri et navigation par catégories ;
- nouvelle fiche produit responsive avec galerie, variantes, quantité, ajout au panier et achat immédiat ;
- panier latéral global qui glisse depuis la droite après un ajout ;
- panier complet avec modification des quantités, suppression, code promo et paiement ;
- recherche globale avec autocomplétion ;
- intégration Stripe Checkout pour le panier et pour « Acheter maintenant » ;
- webhook Stripe et enregistrement local des paiements pour éviter de compter deux fois le stock ;
- historique minimal des ventes permettant d'alimenter la section « Les plus achetés » ;
- pages de succès et d'annulation de paiement ;
- UI globale modernisée et responsive.

## Installation

```bash
python -m venv venv
# Windows : venv\Scripts\activate
# macOS/Linux : source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Le projet peut démarrer sans clé météo ni Stripe, mais le paiement Stripe restera désactivé tant que `STRIPE_SECRET_KEY` n'est pas renseignée.

## Configuration Stripe

Dans `.env`, ajoutez vos clés Stripe de test :

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_CURRENCY=eur
STORE_CURRENCY_SYMBOL=€
```

Pour tester le webhook localement avec Stripe CLI :

```bash
stripe listen --forward-to localhost:8000/api/stripe/webhook/
```

Copiez ensuite le secret `whsec_...` retourné par Stripe CLI dans `STRIPE_WEBHOOK_SECRET`.

Le paiement est créé côté serveur : les prix envoyés à Stripe sont toujours recalculés depuis la base de données, jamais depuis le navigateur. Après confirmation du paiement, le stock est décrémenté une seule fois et la vente est enregistrée.

## Devise

La devise Stripe et le symbole affiché sont configurables séparément :

```env
STRIPE_CURRENCY=eur
STORE_CURRENCY_SYMBOL=€
```

Si vous passez à une autre devise, assurez-vous que les prix présents dans la base correspondent bien à cette devise.

## Important avant production

- utilisez une vraie `SECRET_KEY` ;
- mettez `DEBUG=False` ;
- renseignez précisément `ALLOWED_HOSTS` ;
- utilisez les clés Stripe live uniquement après vos tests ;
- configurez le webhook Stripe sur votre domaine public ;
- servez les fichiers médias via un stockage persistant (Cloudinary/S3 ou volume persistant) ;
- utilisez PostgreSQL pour la production si le trafic augmente.
