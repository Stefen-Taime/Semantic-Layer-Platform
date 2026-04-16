# Business Requirements

Ce document décrit des besoins métier initiaux servant de base à la semantic layer.

## Finance

L'équipe Finance veut suivre la performance économique du service taxi avec un grain quotidien et géographique.

- `gross_revenue` par zone et par jour
- `average_fare` par zone et par jour
- `tip_rate` par zone et par jour

Questions typiques :

- Quel est le revenu brut journalier par zone de pickup ?
- Quelles zones génèrent les fares moyens les plus élevés ?
- Le taux de tip varie-t-il selon le borough ou le type de paiement ?

## Operations

L'équipe Operations veut suivre le volume et l'efficacité du service.

- `completed_trips` par zone
- `average_trip_duration` par zone
- `average_trip_distance` par zone

Questions typiques :

- Quelles zones concentrent le plus de trajets terminés ?
- La durée moyenne de trajet augmente-t-elle selon le moment de la journée ou la zone ?
- Quelle relation observe-t-on entre distance moyenne et borough ?

## Product

L'équipe Product veut mieux comprendre le comportement des passagers et les modes de paiement.

- `payment_type_share`
- distribution de `passenger_count`

Questions typiques :

- Quelle part des trajets est payée par carte versus cash ?
- La distribution du nombre de passagers change-t-elle selon la zone de pickup ?
- Certains segments ont-ils des comportements de paiement distincts ?

## Conséquences pour la modélisation

Ces besoins impliquent au minimum :

- une table de faits certifiée des trajets taxi,
- des dimensions de temps, zone, borough, vendor et payment type,
- des métriques agrégées simples,
- quelques métriques dérivées pour illustrer la couche sémantique.
