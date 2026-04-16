# Hive Configuration

Ce dossier contient les éléments de configuration de base pour le **Hive Metastore**.

Le rôle de Hive dans MetricForge NYC est de centraliser :

- les bases de données,
- les tables batch certifiées,
- les schémas consultés ensuite par Trino.

Le fichier `hive-site.xml.example` est fourni comme point de départ documentaire. Il devra être adapté à l'environnement local ou à la VM GCP.
