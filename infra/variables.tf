variable "location" {
  type    = string
  default = "canadacentral"
}
variable "environment" {
  type    = string
  default = "dev"
  validation {
    condition     = var.environment == "dev"
    error_message = "El bootstrap de este laboratorio crea el ambiente dev."
  }
}
variable "maximum_instance_count" {
  type    = number
  default = 2
  validation {
    condition     = var.maximum_instance_count >= 1 && var.maximum_instance_count <= 3 && floor(var.maximum_instance_count) == var.maximum_instance_count
    error_message = "Usa de 1 a 3 instancias para el laboratorio."
  }
}
variable "extra_tags" {
  type    = map(string)
  default = { demonstration = "baseline" }
}
