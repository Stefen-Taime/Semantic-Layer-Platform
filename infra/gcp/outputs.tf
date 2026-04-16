output "instance_name" {
  description = "Name of the created Compute Engine instance."
  value       = google_compute_instance.metricforge_demo_vm.name
}

output "instance_zone" {
  description = "Zone of the created Compute Engine instance."
  value       = google_compute_instance.metricforge_demo_vm.zone
}

output "instance_external_ip" {
  description = "Public IP address of the demo VM."
  value       = google_compute_instance.metricforge_demo_vm.network_interface[0].access_config[0].nat_ip
}

output "ssh_command" {
  description = "Convenience command to SSH into the demo VM with gcloud."
  value       = "gcloud compute ssh ${google_compute_instance.metricforge_demo_vm.name} --project=${var.project_id} --zone=${var.zone}"
}
