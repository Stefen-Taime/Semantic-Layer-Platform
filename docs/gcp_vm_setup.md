# GCP VM Setup

## Machine recommendation

- minimum: `e2-standard-4` with 16 GB RAM
- recommended for the full demo: `e2-standard-8` with 32 GB RAM

## Why this size

- MinIO + Hive Metastore + PostgreSQL + Trino + API + dashboard fit reasonably on 16 GB
- adding Druid + Airflow makes the memory margin much tighter

## Base install

```bash
sudo apt-get update
sudo apt-get install -y git curl ca-certificates
```

Install Docker:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
newgrp docker
```

Check the Compose plugin:

```bash
docker compose version
```

## Clone the repo

```bash
git clone <repo-url>
cd Semantic-Layer-Platform
```

## Launch the full demo

```bash
bash scripts/run_demo_stack.sh
bash scripts/check_services.sh
```

## Cost and shutdown

- stop the stack when you're done with it:

```bash
bash scripts/stop_demo_stack.sh
```

- stop or delete the VM after the demo to avoid unnecessary costs

## Honest warning

The full stack is a portfolio demo, not a hardened production platform. The credentials are dev-only and some Hive/Druid integrations may need small version tweaks depending on the VM.
