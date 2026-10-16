terraform {
  required_version = "~> 1.16.0"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.0" }
  }
}
provider "azurerm" {
  features {}
  storage_use_azuread             = true
  resource_provider_registrations = "none"
}
variable "github_oidc_subject" {
  type    = string
  default = "repo:IsaacDev2024@158796340/hugo-paco-luis-serverless@1421677306:ref:refs/heads/main"
  validation {
    condition     = endswith(var.github_oidc_subject, ":ref:refs/heads/main") && !strcontains(var.github_oidc_subject, "*")
    error_message = "La confianza OIDC debe identificar exactamente el repositorio y main."
  }
}
variable "location" {
  type    = string
  default = "canadacentral"
}
data "azurerm_client_config" "current" {}
locals {
  suffix = substr(sha256(data.azurerm_client_config.current.subscription_id), 0, 8)
  tags = {
    team        = "Hugo Paco y Luis"
    project     = "segundo-parcial-taller-4"
    environment = "dev"
    managed_by  = "terraform-bootstrap"
  }
}
resource "azurerm_resource_group" "app" {
  name     = "rg-hpl-parcial-dev"
  location = var.location
  tags     = local.tags
}
resource "azurerm_resource_group" "state" {
  name     = "rg-hpl-terraform-state"
  location = var.location
  tags     = local.tags
}
resource "azurerm_storage_account" "state" {
  #checkov:skip=CKV_AZURE_43:El sufijo sha256 se resuelve en Terraform; nombre validado por Azure y las pruebas.
  #checkov:skip=CKV2_AZURE_33:Endpoint público con Entra ID para laboratorio; sin blobs anónimos.
  #checkov:skip=CKV2_AZURE_1:Cifrado administrado por Microsoft; CMK fuera del alcance académico.
  #checkov:skip=CKV_AZURE_33:Backend exclusivamente Blob; no se utilizan colas.
  #checkov:skip=CKV_AZURE_35:Runners GitHub requieren endpoint público autenticado con Entra ID.
  #checkov:skip=CKV_AZURE_59:Sin VNet de laboratorio; no hay blobs públicos ni claves compartidas.
  #checkov:skip=CKV_AZURE_206:LRS con versionado y recuperación de siete días para estado de laboratorio.
  name                             = "sthplstate${local.suffix}"
  resource_group_name              = azurerm_resource_group.state.name
  location                         = var.location
  account_tier                     = "Standard"
  account_replication_type         = "LRS"
  min_tls_version                  = "TLS1_2"
  https_traffic_only_enabled       = true
  allow_nested_items_to_be_public  = false
  shared_access_key_enabled        = false
  default_to_oauth_authentication  = true
  cross_tenant_replication_enabled = false
  tags                             = local.tags
  blob_properties {
    versioning_enabled = true
    delete_retention_policy { days = 7 }
    container_delete_retention_policy { days = 7 }
  }
}
resource "azurerm_role_assignment" "operator_state" {
  scope                = azurerm_storage_account.state.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}
resource "azurerm_storage_container" "state" {
  #checkov:skip=CKV2_AZURE_21:Backend de laboratorio sin lectura de negocio; historial mediante versionado y logs de CI.
  name                  = "tfstate"
  storage_account_id    = azurerm_storage_account.state.id
  container_access_type = "private"
  depends_on            = [azurerm_role_assignment.operator_state]
}
resource "azurerm_user_assigned_identity" "github" {
  for_each            = toset(["infra", "app"])
  name                = "id-github-${each.key}-hpl"
  resource_group_name = azurerm_resource_group.state.name
  location            = var.location
  tags                = local.tags
}
resource "azurerm_federated_identity_credential" "github" {
  for_each                  = azurerm_user_assigned_identity.github
  name                      = "github-main"
  user_assigned_identity_id = each.value.id
  audience                  = ["api://AzureADTokenExchange"]
  issuer                    = "https://token.actions.githubusercontent.com"
  subject                   = var.github_oidc_subject
}
resource "azurerm_role_assignment" "infra" {
  for_each             = toset(["Contributor", "Role Based Access Control Administrator", "Storage Blob Data Contributor"])
  scope                = azurerm_resource_group.app.id
  role_definition_name = each.value
  principal_id         = azurerm_user_assigned_identity.github["infra"].principal_id
}
resource "azurerm_role_assignment" "state" {
  scope                = azurerm_storage_container.state.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.github["infra"].principal_id
}
resource "azurerm_role_assignment" "app" {
  scope                = azurerm_resource_group.app.id
  role_definition_name = "Website Contributor"
  principal_id         = azurerm_user_assigned_identity.github["app"].principal_id
}
output "github_variables" {
  value = {
    AZURE_SUBSCRIPTION_ID  = data.azurerm_client_config.current.subscription_id
    AZURE_TENANT_ID        = data.azurerm_client_config.current.tenant_id
    AZURE_INFRA_CLIENT_ID  = azurerm_user_assigned_identity.github["infra"].client_id
    AZURE_APP_CLIENT_ID    = azurerm_user_assigned_identity.github["app"].client_id
    TF_STATE_ACCOUNT       = azurerm_storage_account.state.name
    TF_STATE_CONTAINER     = azurerm_storage_container.state.name
    AZURE_FUNCTIONAPP_NAME = "func-hpl-dev-${local.suffix}"
  }
}
