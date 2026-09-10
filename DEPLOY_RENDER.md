# Déploiement production — Render + Docker + WhiteNoise + Cloudflare R2

Le projet est prêt pour un déploiement Docker sur Render. Les fichiers **statiques** (`static/`) sont collectés dans l'image et servis par WhiteNoise. Les fichiers **média** (`ImageField`, produits, avis, profils) peuvent être envoyés vers Cloudflare R2 via `django-storages`.

## 1. Cloudflare R2

1. Créez un bucket R2.
2. Créez un token R2 avec accès lecture/écriture limité à ce bucket.
3. Relevez l'Account ID, l'Access Key ID et la Secret Access Key.
4. Pour la production, associez de préférence un domaine personnalisé au bucket, par exemple `media.votredomaine.com`.
5. Renseignez dans Render :
   - `USE_CLOUDFLARE_R2=True`
   - `CLOUDFLARE_R2_ACCOUNT_ID`
   - `CLOUDFLARE_R2_ACCESS_KEY_ID`
   - `CLOUDFLARE_R2_SECRET_ACCESS_KEY`
   - `CLOUDFLARE_R2_BUCKET_NAME`
   - `CLOUDFLARE_R2_CUSTOM_DOMAIN` (sans `https://`, recommandé)

Pour envoyer les médias déjà présents dans le dossier local `media/` vers R2, activez temporairement les variables R2 dans votre environnement local puis lancez :

```bash
python manage.py sync_media_to_storage
```

La commande conserve les chemins relatifs (`products/...`, etc.) afin que les valeurs déjà stockées dans les `ImageField` continuent de fonctionner.

## 2. Render

Le fichier `render.yaml` crée :

- un Web Service Docker ;
- une base PostgreSQL ;
- un health check sur `/health/` ;
- les variables non sensibles ;
- des invites pour les secrets Stripe, Cloudflare et l'adresse du magasin.

Dans Render, créez un **Blueprint** depuis le dépôt contenant ce projet. Lors du premier déploiement, renseignez les variables marquées `sync: false`.

Le conteneur exécute automatiquement `python manage.py migrate --noinput` avant Gunicorn. Les statiques sont déjà collectés au build avec `collectstatic`.

## 3. Adresse Google Maps

Renseignez une adresse réelle dans :

```env
STORE_ADDRESS=Votre adresse complète, Ville, Pays
```

Activez également **Maps Embed API** dans Google Cloud et renseignez une clé restreinte à votre domaine :

```env
GOOGLE_MAPS_EMBED_API_KEY=...
```

La page d'accueil construit alors automatiquement l'iframe Google Maps officielle et le bouton d'itinéraire. Tant que l'adresse ou la clé manque, un état de configuration est affiché à la place d'une localisation inventée.

## 4. Stripe

Renseignez les clés de production dans Render :

```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

Créez ensuite un endpoint webhook Stripe pointant vers :

```text
https://VOTRE-DOMAINE/api/stripe/webhook/
```

## 5. Domaine personnalisé

Si vous ajoutez un domaine à Render, ajoutez aussi ce domaine aux variables :

```env
ALLOWED_HOSTS=.onrender.com,votredomaine.com,www.votredomaine.com
CSRF_TRUSTED_ORIGINS=https://*.onrender.com,https://votredomaine.com,https://www.votredomaine.com
```

N'activez HSTS (`SECURE_HSTS_SECONDS`) qu'après avoir vérifié que le site et tous les sous-domaines concernés fonctionnent bien exclusivement en HTTPS.

## Reçus de commande par Gmail SMTP

Le webhook Stripe confirme le paiement puis Django envoie un reçu HTML au courriel collecté par Stripe Checkout. L'envoi est idempotent grâce au champ `receipt_sent_at` de `PaymentRecord` : une même commande n'est pas envoyée deux fois si le webhook et la page de succès sont appelés tous les deux.

Dans le compte Google utilisé pour les envois, activez la validation en deux étapes puis créez un **mot de passe d'application**. Sur Render, renseignez :

```text
EMAIL_HOST_USER=votre-adresse@gmail.com
EMAIL_HOST_PASSWORD=mot-de-passe-application-google
DEFAULT_FROM_EMAIL=Just Like That <votre-adresse@gmail.com>
SUPPORT_EMAIL=votre-adresse@gmail.com
SEND_ORDER_RECEIPTS=True
```

Le serveur utilise `smtp.gmail.com`, le port `587` et TLS par défaut. Ne mettez jamais le mot de passe Gmail normal dans Render et ne commitez pas le mot de passe d'application dans `.env`.

Après déploiement, appliquez les migrations et testez une commande Stripe en mode test. Dans l'administration Django, `PaymentRecord.receipt_sent_at` permet de vérifier que le reçu a bien été envoyé ; `receipt_error` garde la dernière erreur d'envoi si le SMTP échoue.

## SEO technique

Le projet expose maintenant `/robots.txt` et `/sitemap.xml`, ajoute les URL canoniques, Open Graph/Twitter Cards, le manifest, les favicons, les données structurées `Organization`, `WebSite` et `Product`, et place les pages panier/recherche/paiement en `noindex`. Les anciennes routes `/product/...` et `/cart/` redirigent en permanent vers les URL canoniques françaises afin d'éviter le contenu dupliqué.
