output "dagster_home" {
  description = "Generated local Dagster home path."
  value       = local.dagster_home
}

output "data_root" {
  description = "Generated local data root path used for Delta tables."
  value       = local.data_root
}

output "runtime_env_file" {
  description = "Generated non-secret env file for local commands and Docker Compose."
  value       = local_file.runtime_env.filename
}

output "dagster_url" {
  description = "Local Dagster UI URL when using the documented dev server or Docker Compose service."
  value       = "http://localhost:${var.dagster_port}"
}
