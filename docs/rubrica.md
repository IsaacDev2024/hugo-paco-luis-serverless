# Trazabilidad del enunciado y la rúbrica

Fuente: enunciado del segundo parcial, páginas 1-3 (condiciones, entregables y pesos) y 7 (taller 4). La asignación es **HUGO PACO Y LUIS**, Azure Functions. El documento contempla máximo un día por taller. No asigna al equipo ECS, Docker/Ansible ni rollback del taller 5.

| Criterio | Peso | Implementación y evidencia |
| --- | --- | --- |
| Infraestructura como código | 20 % | `infra/`, `bootstrap/`, lockfiles, backend Blob con lease; artefacto de plan/apply |
| Automatización CI/CD | 25 % | `.github/workflows/ci-cd.yml`, filtros por ruta, publicación automática y verificación de SHA |
| Contenedores y despliegue de aplicación | 15 % | Para el taller 4: ZIP Python, host.json en raíz, Functions Action y One Deploy; Docker no aplica |
| Seguridad y credenciales | 15 % | OIDC, identidades separadas, Storage sin shared keys, HTTPS, Checkov/Trivy bloqueantes y política adicional de Flex |
| Funcionamiento en nube | 15 % | URL pública y evidencia HTTP contra Azure: JSON, texto y errores de validación |
| Documentación, demostración y destrucción | 10 % | README, diagrama, este mapa, decisiones y workflow manual de destrucción |

## Actividades específicas del taller 4

| Actividad | Dónde verificar |
| --- | --- |
| Grupo de recursos, almacenamiento y Function App mediante Terraform | bootstrap crea el grupo; infra crea Storage y Function App |
| Función HTTP con al menos dos tipos de respuesta | `/api/saludo`: application/json y text/plain; HTTP 200/400/413/415 |
| Empaquetado y despliegue automáticos | scripts/package.py y job application |
| Checkov y análisis Trivy de dependencias/archivos | artefactos validacion-SHA; Trivy incluye secretos |
| Variables sin exponer secretos | GitHub Variables solo para identificadores; app settings sin claves Storage |
| Registros básicos | Application Insights, Log Analytics, auditoría Blob |
| URL después del despliegue | Terraform outputs y resumen de GitHub Actions |
| Cambio de función produce nueva publicación automática | release.json cambia de versión; health devuelve SHA de la ejecución |

## Once entregables comunes

1. URL del repositorio: README.
2. URL pública/instrucciones de prueba: evidence/status.json y README.
3. Código de infraestructura: infra/ y bootstrap/.
4. Dockerfile: no aplica al taller asignado.
5. Playbooks Ansible: no aplica al taller asignado.
6. Workflows: CI/CD y destrucción manual.
7. README técnico y diagrama: README, Mermaid reproducible en GitHub.
8. Checkov y Trivy: evidence/local y artefactos reales de CI.
9. Cambio de aplicación publicado: evidence/status.json y artefacto de aplicación con versión/SHA.
10. Cambio de infraestructura aplicado: etiqueta demonstration de config/lab.tfvars, diff de plan y apply de CI.
11. Decisiones, limitaciones y mejoras: docs/decisiones.md.

El estado ejecutado y las URLs de runs se registran en evidence/status.json. Esta matriz expresa cobertura técnica y no predice la nota del docente.
