# Decisiones, seguridad y límites

1. **Flex Consumption, Python 3.11 y paquete ZIP.** Servicio administrado y escalado a cero, suficiente para el taller. Python 3.11 permite reproducir las pruebas de este equipo; futuras actualizaciones deben validar soporte de Azure y dependencias. Se eligió Flex siguiendo el [quickstart oficial](https://learn.microsoft.com/azure/azure-functions/functions-create-first-function-terraform).
2. **Tres identidades.** CI de infraestructura, CI de aplicación y runtime. La federación solo admite main del repositorio configurado. Infra CI requiere Contributor, RBAC Administrator y Blob Data Contributor en el grupo de carga; puede administrar roles dentro de ese grupo y ese permiso merece protección de rama. No es Owner de la suscripción. Aplicación tiene Website Contributor en el grupo para poder consultar y publicar su única Function App. Mejora: asignar este rol a la Function App existente y restringir RBAC a roles/principales concretos.
3. **Storage sin claves.** La identidad del runtime recibe Blob Data Owner en la cuenta de la carga, necesario para los comportamientos del host HTTP y suficiente para el contenedor de despliegue. Sin colas, timers ni bindings adicionales; añadirlos exige revisar roles. `AzureWebJobsStorage__*` son identificadores, no cadenas con claves. [Referencia de identidad](https://learn.microsoft.com/azure/azure-functions/functions-identity-based-connections-tutorial).
4. **Estado separado de la aplicación.** Backend Blob de bootstrap con OAuth, versionado y borrado lógico. La identidad de app no accede al estado. Bootstrap usa estado local privado que debe respaldarse; no se destruye el backend desde el workflow de carga.
5. **Checkov y Trivy bloqueantes.** Se fijan herramientas, acciones por SHA y dependencias. Checkov no cubre todos los atributos de Flex mediante sus controles antiguos; la política CKV2_HPL_1 y terraform test verifican HTTPS, identidad, Basic Auth deshabilitado y límites. El escaneo no garantiza ausencia total de vulnerabilidades.
6. **Actualización de aplicación sin Terraform.** Empaquetar los siete archivos permitidos con SHA en release.json. One Deploy con compilación remota instala las dependencias en Linux y evita empaquetar bibliotecas de macOS. El SHA publicado se comprueba mediante HTTP. [Funciones de la acción](https://github.com/Azure/functions-action).
7. **Acceso público limitado al ejemplo.** La API anónima solo genera saludos; no modifica datos ni tiene operaciones administrativas. Validación de tamaño/tipos, cabeceras de seguridad, CSP y salida por textContent. No hay defensa distribuida contra abuso ni autenticación del visitante. Mejora: APIM/autenticación, límites por consumidor y alertas si se amplía el alcance.
8. **Costo y disponibilidad.** LRS, 512 MB, dos instancias por defecto, sin always-ready, retención de 30 días, ingestión limitada. No hay SLA propio ni recuperación regional. Los límites no son un presupuesto monetario estricto; destruir tras evaluar.

## Excepciones Checkov, acotadas por recurso

No se usa soft-fail ni una exclusión global de Azure. Cada comentario `checkov:skip` incluye su razón y aparece como omitido en la evidencia.

| ID | Motivo en este laboratorio |
| --- | --- |
| CKV_AZURE_33 | Sin colas de negocio; registros de ejecución en Application Insights |
| CKV_AZURE_35 / 59, CKV2_AZURE_33 | Endpoint Storage público autenticado para runners y runtime sin VNet; blobs privados y shared keys deshabilitadas |
| CKV_AZURE_206 | LRS por costo académico; sin réplica regional |
| CKV_AZURE_43 | El analizador no resuelve el sufijo sha256 de la suscripción; Azure y Terraform validan nombres |
| CKV2_AZURE_1 | Cifrado administrado por Microsoft, sin una clave CMK adicional |
| CKV_AZURE_225 / 212 | Flex con escalado a cero, sin instancias fijas ni redundancia zonal; controles concebidos para planes dedicados |
| CKV2_AZURE_21 | Carga: auditoría StorageRead/Write/Delete mediante Monitor diagnostic_setting; el control exige Storage Insights heredado. Backend: historial por versionado/CI, sin auditoría de lecturas de blobs |

## Limitaciones y mejoras

- Retención de evidencias CI de 30 días: conservar copia antes de la entrega.
- No hay rollback automático; pertenece al taller 5. Ante fallo, Actions marca error y conserva evidencia; restaurar una versión conocida mediante revert y nueva ejecución.
- Las pruebas de Terraform simulan el proveedor; las pruebas HTTP reales demuestran la publicación pero no constituyen una prueba de carga.
- Falta protección administrada de main en el repositorio: agregar revisión obligatoria y propietarios de código para `infra/`, `bootstrap/` y workflows si el equipo adopta un proceso de PR.
- Una configuración distinta de región/nombres puede reemplazar recursos. El cambio de infraestructura de la demostración usa exclusivamente tags.
- La destrucción completa debe realizarla el operador después de guardar evidencias; no se simula afirmando que ya se ejecutó.

## Ajuste comprobado de la suscripción

La política sys.regionrestriction de Azure for Students permitió chilecentral, belgiumcentral, francecentral, westus y canadacentral. El primer intento en eastus2 fue rechazado por política (403). Se cambió a canadacentral antes de crear la carga; esto no se resolvió deshabilitando políticas ni controles. En otra suscripción se debe consultar la política y la disponibilidad de Flex.

## Confianza OIDC verificada

GitHub emitió el subject con IDs inmutables y Azure rechazó el subject anterior basado solo en nombres. Se corrigió la federación de ambas identidades para exigir el valor exacto de `sub_claim_prefix` más `:ref:refs/heads/main`. El script prepare_bootstrap consulta el API oficial; no se usan comodines ni se deshabilita el formato inmutable. [Referencia oficial](https://docs.github.com/en/actions/reference/security/oidc).

## Corrección reproducible de AzureRM 4.81.0

El proveedor agrega AzureWebJobsStorage con una clave vacía al crear/actualizar Flex incluso cuando el contenedor de despliegue usa identidad. El valor directo tiene prioridad sobre AzureWebJobsStorage__* y provocó AuthenticationFailed al sincronizar el host. terraform_data.identity_storage retira únicamente ese valor mediante Azure CLI después de crear o modificar la Function App (replace_triggered_by); conserva las conexiones de identidad y no habilita shared keys. El comando es idempotente, no imprime valores y requiere la sesión Azure ya disponible en CI. Es un workaround acotado de proveedor; una mejora futura es retirarlo cuando el proveedor gestione nativamente esta combinación sin inyectar la cadena. [Implementación del proveedor](https://github.com/hashicorp/terraform-provider-azurerm/blob/v4.81.0/internal/services/appservice/function_app_flex_consumption_resource.go).
