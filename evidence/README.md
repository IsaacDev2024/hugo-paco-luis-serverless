# Evidencias del taller 4

`status.json` es el índice de resultados y URLs. Las pruebas locales se distinguen de las comprobaciones públicas en Azure.

- `local/`: pruebas Python, Terraform, Checkov, Trivy y una vista previa WSGI. No prueba publicación en Azure.
- `cloud/baseline/`: primera infraestructura aplicada (9 recursos) y 8 pruebas HTTP manuales de v1.0.0, cuyo portal estaba en /home. El run inicial falló en la comprobación de la raíz del portal; su run.json conserva ese resultado real. La entrega final usa la raíz / explícita.
- `cloud/app-change/`: cambio de release.json con infraestructura omitida y nueva versión publicada.
- `cloud/infra-change/`: cambio de tags en config/lab.tfvars, repetición automática del ajuste de identidad, plan/apply y comprobación pública posteriores.
- `cloud/storage-fix/`: ejecución completa exitosa que incorpora la corrección de AzureRM y lectura compatible del hostname.
- `cloud/infra-initial/`: primer cambio aplicado de seis etiquetas; el run falló posteriormente al leer el hostname. Se conserva la comprobación HTTP manual exitosa de ese despliegue.
- `cloud/final-validation/`: última validación después de documentar las evidencias, cuando esté disponible.

Cada carpeta cloud contiene run.json con URL, SHA, jobs y pasos, junto a los artefactos descargados de GitHub Actions. El reporte smoke incluye la versión y el SHA realmente recibidos por HTTP. Comparar esos valores con headSha; nunca usar el campo commit=local como prueba de despliegue.

Checkov reporta controles pasados y omitidos por separado. Trivy se ejecuta con umbral HIGH/CRITICAL y escaneo de secretos; cero hallazgos a ese umbral no significa ausencia de problemas de otras severidades. Las excepciones están explicadas en docs/decisiones.md.

Para conservar una nueva ejecución finalizada:

```bash
python scripts/collect_evidence.py NUMERO_DE_RUN baseline
# Las otras etiquetas admitidas son app-change, infra-change, final-validation, storage-fix e infra-initial.
```

Los artefactos remotos caducan a los 30 días. Estas copias permiten su inspección después. No incluir estados Terraform, planes binarios, llaves privadas, tokens ni archivos de configuración local. Las capturas del portal son apoyo visual y no sustituyen los reportes HTTP.
