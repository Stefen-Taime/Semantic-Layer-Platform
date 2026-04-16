variable "project_id" {
  description = "GCP project ID where the demo VM will be created."
  type        = string
}

variable "region" {
  description = "GCP region used by the provider."
  type        = string
  default     = "northamerica-northeast1"
}

variable "zone" {
  description = "GCP zone where the demo VM will be created."
  type        = string
  default     = "northamerica-northeast1-b"
}

variable "environment" {
  description = "Environment label applied to the VM."
  type        = string
  default     = "demo"
}

variable "instance_name" {
  description = "Name of the MetricForge demo VM."
  type        = string
  default     = "metricforge-demo-vm"
}

variable "machine_type" {
  description = "Compute Engine machine type."
  type        = string
  default     = "e2-standard-8"
}

variable "boot_disk_size_gb" {
  description = "Boot disk size in GB."
  type        = number
  default     = 100
}

variable "boot_disk_type" {
  description = "Boot disk type."
  type        = string
  default     = "pd-balanced"
}

variable "network_name" {
  description = "Existing VPC network name to attach the VM to."
  type        = string
  default     = "default"
}

variable "network_tags" {
  description = "Network tags applied to the VM and used by firewall rules."
  type        = list(string)
  default     = ["metricforge-demo"]
}

variable "create_firewall_rules" {
  description = "Whether Terraform should create SSH and demo app firewall rules."
  type        = bool
  default     = true
}

variable "ssh_source_ranges" {
  description = "CIDR ranges allowed to reach SSH on port 22."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "app_source_ranges" {
  description = "CIDR ranges allowed to reach FastAPI, Streamlit, Airflow, Trino, Druid, and MinIO Console."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
