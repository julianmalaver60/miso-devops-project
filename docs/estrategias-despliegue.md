# Estrategias de despliegue en Elastic Beanstalk

Responsable: **María José**. Corresponde al ítem 2 del documento (20 %): ejecutar **4
estrategias distintas** con más de una instancia (auto scaling mín. 3, máx. 6) y documentar
cada una.

## Cómo hacer cada despliegue

1. Subir el número de versión en `blacklist_api/__init__.py` (`__version__ = "1.0.1"`, luego
   `"1.0.2"`, …), hacer commit y generar el paquete:
   ```bash
   git archive -o blacklist-v1.0.1.zip HEAD
   ```
2. Elegir la estrategia: *Configuration → Rolling updates and deployments → Deployment policy*
   (y el tamaño del lote cuando aplique).
3. *Upload and deploy* del `.zip` nuevo.
4. Mientras despliega, consultar `/health` en bucle para ver qué instancias (`host`) ya
   responden con la versión nueva (`version`):

   Git Bash:
   ```bash
   while true; do curl -s http://<url-del-ambiente>/health; echo " $(date +%T)"; sleep 1; done
   ```
   PowerShell:
   ```powershell
   while ($true) { (Invoke-RestMethod http://<url-del-ambiente>/health) | ConvertTo-Json -Compress; Start-Sleep 1 }
   ```
5. Tomar el tiempo de la pestaña **Events** del ambiente: desde *Environment update is
   starting* hasta *Environment update completed successfully*.

## Qué esperar de cada estrategia

Según la documentación de AWS (*Deployment policies and settings*). Confirmar con lo observado:
eso es lo que se documenta.

| Estrategia | ¿Instancias nuevas? | ¿Baja el servicio? |
|---|---|---|
| All at once | No, las mismas | Sí, unos segundos |
| Rolling | No, por lotes | No, pero con menos capacidad |
| Rolling with additional batch | Lanza un lote extra temporal | No, capacidad completa |
| Immutable | Sí, un grupo nuevo completo | No |
| Traffic splitting | Sí, y reparte tráfico por porcentaje | No |

Immutable y Traffic splitting duplican instancias por un rato: cuestan más. Hacer las 4
estrategias en una misma sesión y apagar todo al terminar.

## Plantilla por estrategia

Copiar una vez por estrategia en el documento.

### Estrategia: _____

| Dato (requisito del enunciado) | Valor |
|---|---|
| a. Instancias utilizadas | |
| b. Cómo se validó que el despliegue estaba en ejecución | |
| c. Tiempo total (mm:ss) | |
| d. ¿Sobre instancias iniciales o nuevas? | |
| e. Capturas de la consola | Events, Health, EC2 |
| f. Hallazgos | |

Versión desplegada: `____` → `____` · Configuración (lote, porcentaje): ____
