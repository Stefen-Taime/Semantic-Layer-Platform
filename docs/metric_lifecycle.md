# Metric Lifecycle

MetricForge NYC suit un cycle simple pour faire passer une demande métier jusqu'à une exposition API ou dashboard.

## Étapes

1. **Business need**
   Une équipe formule un besoin clair, par exemple "suivre le revenu brut journalier par zone".
2. **Metric definition**
   La métrique est définie fonctionnellement : formule, grain attendu, dimensions autorisées, exclusions éventuelles.
3. **YAML config**
   La définition est traduite dans les fichiers `entities.yml`, `dimensions.yml`, `joins.yml` et `metrics.yml`.
4. **Validation**
   Le moteur vérifie la cohérence du modèle : références d'entités, dimensions autorisées, métriques dérivées, joins connus.
5. **Query generation**
   Une requête SQL est générée pour Spark, Trino ou Druid selon le mode d'exécution ciblé.
6. **Execution**
   Le moteur exécute la requête ou retourne une réponse mockée tant que l'intégration réelle n'est pas branchée.
7. **API**
   La métrique est accessible via un endpoint de catalogue ou de requête.
8. **Dashboard**
   Le dashboard consomme la définition validée et affiche le résultat de façon cohérente.

## Résultat attendu

Ce cycle réduit le risque que :

- deux équipes utilisent des définitions différentes,
- les dashboards embarquent des calculs cachés,
- les changements de logique soient faits sans validation formelle.

## Gouvernance future

Dans les prochains prompts, ce cycle pourra être renforcé par :

- tests automatisés sur la semantic layer,
- versionnement des métriques,
- vérifications de compatibilité arrière,
- génération d'un catalogue lisible par les consommateurs.
