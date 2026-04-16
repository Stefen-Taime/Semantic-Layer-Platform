# GCP Demo VM

Ce dossier crée une VM Compute Engine pour exécuter la démo complète `MetricForge NYC`.

## Ressources créées

- 1 VM Compute Engine
  - nom : `metricforge-demo-vm`
  - machine type : `e2-standard-8`
  - image : Ubuntu 22.04 LTS
  - boot disk : `100 GB`
  - network tags : `metricforge-demo`
- règles firewall optionnelles
  - `22` SSH
  - `8000` FastAPI
  - `8501` Streamlit
  - `8081` Airflow
  - `8080` Trino
  - `8888` Druid
  - `9001` MinIO Console

Le startup script installe :

- Docker
- Docker Compose plugin
- Git
- curl
- wget
- unzip
- make

## Prérequis

- Terraform `>= 1.5`
- `gcloud` installé
- un projet GCP existant

Si tu as déjà une auth GCP active dans le terminal, Terraform peut souvent la réutiliser via les credentials applicatifs. Le plus fiable reste :

```bash
gcloud auth application-default login
```

## Utilisation

Depuis la racine du repo :

```bash
cd infra/gcp
terraform init
terraform plan -var="project_id=<GCP_PROJECT_ID>"
terraform apply -var="project_id=<GCP_PROJECT_ID>"
```

## Variables utiles

- `project_id` : obligatoire
- `region` : défaut `northamerica-northeast1`
- `zone` : défaut `northamerica-northeast1-b`
- `instance_name` : défaut `metricforge-demo-vm`
- `machine_type` : défaut `e2-standard-8`
- `create_firewall_rules` : défaut `true`
- `ssh_source_ranges` : défaut `["0.0.0.0/0"]`
- `app_source_ranges` : défaut `["0.0.0.0/0"]`

Pour restreindre l'accès :

```bash
terraform apply \
  -var="project_id=<GCP_PROJECT_ID>" \
  -var='ssh_source_ranges=["<YOUR_IP>/32"]' \
  -var='app_source_ranges=["<YOUR_IP>/32"]'
```

## Après création

Récupère la commande SSH :

```bash
terraform output ssh_command
```

Puis sur la VM :

```bash
git clone https://github.com/Stefen-Taime/Semantic-Layer-Platform.git
cd Semantic-Layer-Platform
./scripts/run_demo_stack.sh
```

## Sortie

Quand la démo est finie :

```bash
terraform destroy -var="project_id=<GCP_PROJECT_ID>"
```

## Limites honnêtes

- les règles firewall sont ouvertes par défaut pour simplifier la démo ; restreins-les avant exposition publique
- la VM créée est pensée pour la démo portfolio, pas pour de la production
- la stack complète reste gourmande ; `e2-standard-8` est un compromis raisonnable, pas un surdimensionnement
