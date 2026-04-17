# GCP Demo VM

This folder provisions a Compute Engine VM to run the full `MetricForge NYC` demo.

## Resources created

- 1 Compute Engine VM
  - name: `metricforge-demo-vm`
  - machine type: `e2-standard-8`
  - image: Ubuntu 22.04 LTS
  - boot disk: `100 GB`
  - network tags: `metricforge-demo`
- optional firewall rules
  - `22` SSH
  - `8000` FastAPI
  - `8501` Streamlit
  - `8081` Airflow
  - `8080` Trino
  - `8888` Druid
  - `9001` MinIO Console

The startup script installs:

- Docker
- Docker Compose plugin
- Git
- curl
- wget
- unzip
- make

## Prerequisites

- Terraform `>= 1.5`
- `gcloud` installed
- an existing GCP project

If you already have an active GCP auth in your terminal, Terraform can usually reuse it through application-default credentials. The most reliable flow is:

```bash
gcloud auth application-default login
```

## Usage

From the repo root:

```bash
cd infra/gcp
terraform init
terraform plan -var="project_id=<GCP_PROJECT_ID>"
terraform apply -var="project_id=<GCP_PROJECT_ID>"
```

## Useful variables

- `project_id`: required
- `region`: default `northamerica-northeast1`
- `zone`: default `northamerica-northeast1-b`
- `instance_name`: default `metricforge-demo-vm`
- `machine_type`: default `e2-standard-8`
- `create_firewall_rules`: default `true`
- `ssh_source_ranges`: default `["0.0.0.0/0"]`
- `app_source_ranges`: default `["0.0.0.0/0"]`

To restrict access:

```bash
terraform apply \
  -var="project_id=<GCP_PROJECT_ID>" \
  -var='ssh_source_ranges=["<YOUR_IP>/32"]' \
  -var='app_source_ranges=["<YOUR_IP>/32"]'
```

## After creation

Fetch the SSH command:

```bash
terraform output ssh_command
```

Then on the VM:

```bash
git clone https://github.com/Stefen-Taime/Semantic-Layer-Platform.git
cd Semantic-Layer-Platform
./scripts/run_demo_stack.sh
```

## Teardown

When the demo is over:

```bash
terraform destroy -var="project_id=<GCP_PROJECT_ID>"
```

## Honest limits

- the firewall rules are open by default to keep the demo simple; tighten them before any public exposure
- the VM created here targets the portfolio demo, not production workloads
- the full stack is still heavy; `e2-standard-8` is a reasonable compromise, not an overkill
