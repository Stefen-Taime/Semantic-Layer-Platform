# Local Vs GCP VM

MetricForge NYC est conçu pour avancer en deux temps : développement léger en local, puis démonstration plus complète sur VM GCP.

## Local Mac 8 Go

Usage recommandé :

- éditer les fichiers YAML de semantic layer,
- développer l'API FastAPI,
- construire le dashboard Streamlit,
- écrire les tests unitaires,
- faire des essais sur de petits échantillons de données.

Limites :

- Spark local reste possible mais doit être limité,
- Hive, Trino et Druid en parallèle peuvent devenir trop lourds,
- ingestion et traitements complets des datasets TLC sont à éviter.

## GCP VM Ubuntu 16 Go / 32 Go

Usage recommandé :

- lancer Spark avec plus de confort pour l'ingestion batch,
- exécuter Hive Metastore et Trino pour une démo réaliste,
- ajouter Druid seulement si nécessaire pour une démonstration OLAP,
- servir l'API et le dashboard sur la même VM pour une architecture compacte.

Recommandation pratique :

- **16 Go RAM** : suffisant pour Spark local modéré + Hive Metastore + Trino + API/dashboard.
- **32 Go RAM** : préférable si Druid est activé ou si les données traitées sont moins échantillonnées.

## Stratégie de progression

- Commencer par Trino comme moteur principal de serving.
- Introduire Druid plus tard uniquement si le bénéfice démonstratif est clair.
- Garder les jeux de données et la volumétrie contrôlés au début.
- Favoriser des composants simples à opérer sur une seule VM.
