# jlt

JLT est une boutique en ligne avec un système de panier robuste conçue pour gérer les stocks en fonctions des variantes de chaque produit. EX: une chaussure peux avoir deux variantes: chaussure nike noir/taille 38 ou chaussure nike noir/taille 25.

Il y a une barre de recherche de produits qui récupère des mots clés et les recherches dans le nom, la description et autres parametres du produit. Le résultat de la recherche est null si il n y a pas de similitude.

Si il y a plus de quatre produit en base, la pagination est activée car le système accèpte 4 produits par page. La pagination est gérer par le module Paginator de Django.

Il est possible pour un utilistateur de laisser un commentaire(avis) sur un produit ainsi qu'une note directement dans la page de détails du produit en question. 

