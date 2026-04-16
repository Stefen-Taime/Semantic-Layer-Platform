# Druid Serving Layer

Apache Druid sert ici de couche OLAP rapide pour quelques métriques pré-agrégées.

## Pourquoi Druid

- latence plus faible sur datasets déjà agrégés
- bon support de requêtes dashboard
- complément crédible à Trino dans une architecture data platform

## Trino vs Druid

- **Trino** : flexible, riche pour l'ad hoc, meilleur pour parcourir les tables certifiées
- **Druid** : rapide sur des datasources pré-agrégées, meilleur pour un serving ciblé

## Métriques dirigées vers Druid

- `daily_zone_revenue`
- `daily_completed_trips`

## Ingestion

Les specs dans `druid/ingestion_specs/` supposent qu'un export intermédiaire a produit des fichiers agrégés journaliers ou par zone.

## Limites

- il faut préparer les jeux agrégés avant ingestion
- la configuration exacte du conteneur Druid peut dépendre de la version d'image
- Druid rend la stack nettement plus lourde en mémoire
