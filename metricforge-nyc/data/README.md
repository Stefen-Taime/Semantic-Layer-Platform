# Data Directory

Ce dossier n'est plus le backend principal de stockage pour le pipeline batch.

Le projet utilise désormais **MinIO** comme stockage objet compatible S3 pour :

- les fichiers sources bruts NYC TLC,
- le warehouse Spark/Hive,
- les tables gérées par la couche batch.

Ce répertoire peut rester pour :

- des placeholders de structure,
- de petits exports manuels,
- des fichiers temporaires non critiques si nécessaire.
