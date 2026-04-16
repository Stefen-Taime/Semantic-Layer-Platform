terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

data "google_compute_image" "ubuntu_2204" {
  family  = "ubuntu-2204-lts"
  project = "ubuntu-os-cloud"
}

data "google_compute_network" "selected" {
  name = var.network_name
}

resource "google_compute_instance" "metricforge_demo_vm" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone
  tags         = var.network_tags

  boot_disk {
    initialize_params {
      image = data.google_compute_image.ubuntu_2204.self_link
      size  = var.boot_disk_size_gb
      type  = var.boot_disk_type
    }
  }

  network_interface {
    network = data.google_compute_network.selected.id

    access_config {}
  }

  metadata_startup_script = file("${path.module}/startup.sh")

  labels = {
    app         = "metricforge"
    environment = var.environment
  }
}

resource "google_compute_firewall" "metricforge_demo_ssh" {
  count   = var.create_firewall_rules ? 1 : 0
  name    = "${var.instance_name}-ssh"
  network = data.google_compute_network.selected.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = var.ssh_source_ranges
  target_tags   = var.network_tags
}

resource "google_compute_firewall" "metricforge_demo_apps" {
  count   = var.create_firewall_rules ? 1 : 0
  name    = "${var.instance_name}-apps"
  network = data.google_compute_network.selected.name

  allow {
    protocol = "tcp"
    ports = [
      "8000",
      "8080",
      "8081",
      "8501",
      "8888",
      "9001",
    ]
  }

  source_ranges = var.app_source_ranges
  target_tags   = var.network_tags
}
