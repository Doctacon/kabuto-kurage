locals {
  project_root          = abspath("${path.module}/../..")
  local_state_root      = "${local.project_root}/${var.local_state_dir}"
  dagster_home          = "${local.local_state_root}/dagster"
  data_root             = "${local.local_state_root}/data"
  runtime_dir           = "${local.local_state_root}/runtime"
  tenant_config_abspath = abspath("${local.project_root}/${var.tenant_config_path}")
}

resource "local_file" "dagster_yaml" {
  filename             = "${local.dagster_home}/dagster.yaml"
  file_permission      = "0644"
  directory_permission = "0755"

  content = templatefile("${path.module}/templates/dagster.yaml.tftpl", {
    telemetry_enabled = var.dagster_telemetry_enabled
  })
}

resource "local_file" "runtime_env" {
  filename             = "${local.runtime_dir}/kabuto.env"
  file_permission      = "0644"
  directory_permission = "0755"

  content = templatefile("${path.module}/templates/kabuto.env.tftpl", {
    dagster_home            = local.dagster_home
    data_root               = local.data_root
    tenant_config_path      = local.tenant_config_abspath
    github_max_repositories = var.github_max_repositories
    dagster_port            = var.dagster_port
  })
}

resource "local_file" "data_readme" {
  filename             = "${local.data_root}/README.md"
  file_permission      = "0644"
  directory_permission = "0755"

  content = <<-EOT
  # Local Generated Data

  This ignored directory is prepared by `terraform -chdir=iac/local apply` for local kabuto-kurage runs.

  Expected Delta table root:

  ```text
  ${local.data_root}/delta/tenants/{tenant_id}/{layer}/github/{table_name}
  ```

  Do not commit generated Delta tables, Dagster run metadata, or local secrets.
  EOT
}
