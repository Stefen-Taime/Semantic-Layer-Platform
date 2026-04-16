# GCP VM Setup

## Recommandation machine

- minimum : `e2-standard-4` avec 16 Go RAM
- recommandé pour la démo complète : `e2-standard-8` avec 32 Go RAM

## Pourquoi cette taille

- MinIO + Hive Metastore + PostgreSQL + Trino + API + dashboard tiennent raisonnablement sur 16 Go
- ajouter Druid + Airflow rend la marge mémoire beaucoup plus serrée

## Installation de base

```bash
sudo apt-get update
sudo apt-get install -y git curl ca-certificates
```

Installer Docker :

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
newgrp docker
```

Vérifier le plugin Compose :

```bash
docker compose version
```

## Cloner le repo

```bash
git clone <repo-url>
cd Semantic-Layer-Platform
```

## Lancer la démo complète

```bash
bash scripts/run_demo_stack.sh
bash scripts/check_services.sh
```

## Coût et arrêt

- stoppe la stack quand tu ne l'utilises plus :

```bash
bash scripts/stop_demo_stack.sh
```

- arrête ou supprime la VM après la démonstration pour éviter des coûts inutiles

## Avertissement honnête

La stack complète est une démo portfolio, pas une plateforme de production durcie. Les credentials sont dev-only et certaines intégrations Hive/Druid peuvent demander de petits ajustements de version selon la VM.
