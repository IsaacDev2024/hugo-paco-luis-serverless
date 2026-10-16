output "function_app_name" { value = azurerm_function_app_flex_consumption.app.name }
output "resource_group_name" { value = data.azurerm_resource_group.app.name }
output "base_url" { value = "https://${azurerm_function_app_flex_consumption.app.default_hostname}" }
output "function_url" { value = "https://${azurerm_function_app_flex_consumption.app.default_hostname}/api/saludo" }
output "health_url" { value = "https://${azurerm_function_app_flex_consumption.app.default_hostname}/api/health" }
output "application_insights_name" { value = azurerm_application_insights.app.name }
