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

## Topologie Docker

La stack Docker Druid du projet utilise désormais une topologie multi-services :

- `druid-zookeeper`
- `druid-postgres`
- `druid-coordinator`
- `druid-broker`
- `druid-historical`
- `druid-middlemanager`
- `druid` : routeur et console

Cette organisation est plus proche du quickstart Docker officiel Druid qu'un conteneur unique bricolé.

## Limites

- il faut préparer les jeux agrégés avant ingestion
- Druid rend la stack nettement plus lourde en mémoire
- la topologie reste une démo monomachine, pas un cluster haute disponibilité
