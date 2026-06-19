variable "local_state_dir" {
  description = "Repository-relative ignored directory where Terraform prepares local runtime files."
  type        = string
  default     = ".local"
}

variable "dagster_port" {
  description = "Host/container port used by the optional local Dagster Docker Compose service."
  type        = number
  default     = 3000
}

variable "dagster_telemetry_enabled" {
  description = "Whether Dagster telemetry should be enabled in the generated local dagster.yaml."
  type        = bool
  default     = false
}

variable "tenant_config_path" {
  description = "Repository-relative tenant config path exported into the generated local env file. Use ignored config/tenants.local.yaml for local overrides."
  type        = string
  default     = "config/tenants.example.yaml"
}

variable "github_max_repositories" {
  description = "Safe default repository cap for demos. Empty string disables the cap."
  type        = string
  default     = "1"
}
