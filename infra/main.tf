locals {
  suffix = substr(sha256(data.azurerm_client_config.current.subscription_id), 0, 8)
  name   = "hpl-${var.environment}-${local.suffix}"
  tags = merge(var.extra_tags, {
    team        = "Hugo Paco y Luis"
    project     = "segundo-parcial-taller-4"
    environment = var.environment
    managed_by  = "terraform"
  })
}
data "azurerm_resource_group" "app" { name = "rg-hpl-parcial-${var.environment}" }

resource "azurerm_storage_account" "app" {
  #checkov:skip=CKV_AZURE_43:El sufijo sha256 se resuelve en Terraform; nombre validado por Azure y las pruebas.
  #checkov:skip=CKV2_AZURE_33:Endpoint público con Entra ID para laboratorio; sin blobs anónimos.
  #checkov:skip=CKV2_AZURE_1:Cifrado administrado por Microsoft; CMK fuera del alcance académico.
  #checkov:skip=CKV_AZURE_33:HTTP solamente; no hay colas de negocio. Telemetría en Application Insights.
  #checkov:skip=CKV_AZURE_35:Red pública autenticada requerida por runners GitHub y Functions sin VNet en este laboratorio.
  #checkov:skip=CKV_AZURE_59:Red pública autenticada; blobs privados y claves compartidas deshabilitadas.
  #checkov:skip=CKV_AZURE_206:LRS es una decisión de costo de laboratorio, no una promesa de recuperación regional.
  name                             = "sthplapp${local.suffix}${var.environment}"
  resource_group_name              = data.azurerm_resource_group.app.name
  location                         = var.location
  account_tier                     = "Standard"
  account_replication_type         = "LRS"
  min_tls_version                  = "TLS1_2"
  https_traffic_only_enabled       = true
  allow_nested_items_to_be_public  = false
  shared_access_key_enabled        = false
  default_to_oauth_authentication  = true
  public_network_access_enabled    = true
  cross_tenant_replication_enabled = false
  tags                             = local.tags
  blob_properties {
    versioning_enabled = true
    delete_retention_policy { days = 7 }
    container_delete_retention_policy { days = 7 }
  }
}
resource "azurerm_storage_container" "deployment" {
  #checkov:skip=CKV2_AZURE_21:Auditoría Blob implementada con Azure Monitor diagnostic_setting StorageRead/Write/Delete; el check exige Storage Insights heredado.
  name                  = "function-releases"
  storage_account_id    = azurerm_storage_account.app.id
  container_access_type = "private"
}
resource "azurerm_user_assigned_identity" "runtime" {
  name                = "id-runtime-${local.name}"
  resource_group_name = data.azurerm_resource_group.app.name
  location            = var.location
  tags                = local.tags
}
resource "azurerm_role_assignment" "runtime_blob" {
  scope                = azurerm_storage_account.app.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = azurerm_user_assigned_identity.runtime.principal_id
}
resource "azurerm_log_analytics_workspace" "app" {
  name                = "log-${local.name}"
  resource_group_name = data.azurerm_resource_group.app.name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  daily_quota_gb      = 0.1
  tags                = local.tags
}
resource "azurerm_application_insights" "app" {
  name                 = "appi-${local.name}"
  resource_group_name  = data.azurerm_resource_group.app.name
  location             = var.location
  workspace_id         = azurerm_log_analytics_workspace.app.id
  application_type     = "web"
  retention_in_days    = 30
  daily_data_cap_in_gb = 0.1
  tags                 = local.tags
}
resource "azurerm_service_plan" "app" {
  #checkov:skip=CKV_AZURE_225:Flex bajo demanda sin instancias always-ready; redundancia zonal no requerida en laboratorio.
  #checkov:skip=CKV_AZURE_212:Flex escala a cero; mantener instancias fijas altera el objetivo y el costo.
  name                = "plan-${local.name}"
  resource_group_name = data.azurerm_resource_group.app.name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "FC1"
  tags                = local.tags
}
resource "azurerm_function_app_flex_consumption" "app" {
  name                                           = "func-${local.name}"
  resource_group_name                            = data.azurerm_resource_group.app.name
  location                                       = var.location
  service_plan_id                                = azurerm_service_plan.app.id
  storage_container_type                         = "blobContainer"
  storage_container_endpoint                     = "${azurerm_storage_account.app.primary_blob_endpoint}${azurerm_storage_container.deployment.name}"
  storage_authentication_type                    = "UserAssignedIdentity"
  storage_user_assigned_identity_id              = azurerm_user_assigned_identity.runtime.id
  runtime_name                                   = "python"
  runtime_version                                = "3.11"
  maximum_instance_count                         = var.maximum_instance_count
  instance_memory_in_mb                          = 512
  http_concurrency                               = 4
  https_only                                     = true
  webdeploy_publish_basic_authentication_enabled = false
  tags                                           = local.tags
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.runtime.id]
  }
  app_settings = {
    APP_ENVIRONMENT                  = var.environment
    TEAM_NAME                        = "Hugo, Paco y Luis"
    AzureWebJobsStorage__accountName = azurerm_storage_account.app.name
    AzureWebJobsStorage__credential  = "managedidentity"
    AzureWebJobsStorage__clientId    = azurerm_user_assigned_identity.runtime.client_id
  }
  site_config {
    application_insights_connection_string = azurerm_application_insights.app.connection_string
    minimum_tls_version                    = "1.2"
    scm_minimum_tls_version                = "1.2"
    http2_enabled                          = true
    remote_debugging_enabled               = false
  }
  depends_on = [azurerm_role_assignment.runtime_blob]
}

resource "azurerm_monitor_diagnostic_setting" "storage_blob" {
  name                       = "blob-audit"
  target_resource_id         = "${azurerm_storage_account.app.id}/blobServices/default"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.app.id
  enabled_log { category = "StorageRead" }
  enabled_log { category = "StorageWrite" }
  enabled_log { category = "StorageDelete" }
}

# AzureRM 4.81.0 agrega AzureWebJobsStorage con una clave vacía incluso al
# elegir UserAssignedIdentity. Esa cadena tiene prioridad sobre AzureWebJobsStorage__*.
# Retirarla después de cada actualización conserva la autenticación por identidad.
resource "terraform_data" "identity_storage" {
  lifecycle {
    replace_triggered_by = [azurerm_function_app_flex_consumption.app]
  }
  provisioner "local-exec" {
    command = "az functionapp config appsettings delete --resource-group \"$HPL_RESOURCE_GROUP\" --name \"$HPL_FUNCTION_APP\" --setting-names AzureWebJobsStorage --output none"
    environment = {
      HPL_RESOURCE_GROUP = data.azurerm_resource_group.app.name
      HPL_FUNCTION_APP   = azurerm_function_app_flex_consumption.app.name
    }
  }
}
