mock_provider "azurerm" {
  mock_data "azurerm_client_config" {
    defaults = {
      subscription_id = "00000000-0000-0000-0000-000000000001"
    }
  }
}
run "secure_lab_defaults" {
  command = plan
  assert {
    condition     = azurerm_storage_account.app.shared_access_key_enabled == false && azurerm_storage_account.app.allow_nested_items_to_be_public == false
    error_message = "Storage debe usar identidad y bloquear objetos públicos."
  }
  assert {
    condition     = azurerm_function_app_flex_consumption.app.https_only && !azurerm_function_app_flex_consumption.app.webdeploy_publish_basic_authentication_enabled
    error_message = "Functions requiere HTTPS y despliegue sin autenticación básica."
  }
  assert {
    condition     = azurerm_function_app_flex_consumption.app.storage_authentication_type == "UserAssignedIdentity"
    error_message = "El despliegue debe usar identidad administrada."
  }
  assert {
    condition     = azurerm_function_app_flex_consumption.app.maximum_instance_count <= 3 && azurerm_function_app_flex_consumption.app.instance_memory_in_mb == 512
    error_message = "Mantener los límites de recursos del laboratorio."
  }
  assert {
    condition     = azurerm_storage_account.app.tags.team == "Hugo Paco y Luis" && azurerm_storage_account.app.tags.project == "segundo-parcial-taller-4" && azurerm_storage_account.app.tags.environment == "dev"
    error_message = "Las etiquetas obligatorias no deben sobrescribirse."
  }
}
run "reject_excessive_scale" {
  command = plan
  variables { maximum_instance_count = 50 }
  expect_failures = [var.maximum_instance_count]
}
