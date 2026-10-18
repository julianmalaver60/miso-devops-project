# Estrategias de despliegue en Elastic Beanstalk

Ejecutar **4 estrategias distintas** con más de una instancia (auto scaling mín. 3, máx. 6) y documentar cada una. Ejecutado el 16 de octubre de 2026 sobre el ambiente `Miso-devops-project-env` (ALB + 3 instancias `t3.micro`, Python 3.12 en Amazon Linux 2023).

## Resultados

| Estrategia | Versión | Instancias usadas | Iniciales o nuevas | Tiempo (mm:ss) | ¿Caída? |
|---|---|---|---|---|---|
| All at once | 1.0.0 → 1.0.1 | 3 | Iniciales | 01:03 | Sí, ~5 s (HTTP 502) |
| Rolling | 1.0.1 → 1.0.2 | 3 | Iniciales (1 por lote) | 09:25 | No (0 errores) |
| Rolling with additional batch | 1.0.2 → 1.0.3 | 4 (3 + 1 temporal) | Mixtas: 1 nueva + 2 iniciales | 09:23 | No (0 errores) |
| Immutable | 1.0.3 → 1.0.4 | 6 (3 + 3 nuevas) | Nuevas (las 3) | 17:50 | No (0 errores) |

El tiempo va de *Environment update is starting* a *Environment update completed
successfully* en la pestaña **Eventos**. El análisis completo, con capturas, está en el
documento de la entrega (sección 2).

## Procedimiento

### 1. Preparar los paquetes

Una versión por estrategia: subir `__version__` en `blacklist_api/__init__.py`, hacer commit
y generar el `.zip` desde ese commit (`git archive` deja los archivos en la raíz del zip, como
los espera Beanstalk):

```bash
git archive -o blacklist-v1.0.1.zip HEAD
```

`/health` devuelve esa versión y el `host` que respondió, así se ve qué instancia ya tiene
el código nuevo.

### 2. Cambiar la política de despliegue

*Configuración → Supervisión y actualizaciones → Editar → Implementaciones*. La consola en
español usa estos nombres:

| Consola en español | Política (AWS) | Lote usado |
|---|---|---|
| Todo a la vez | All at once | — |
| Continua | Rolling | Fijo, 1 |
| Continua con lote adicional | Rolling with additional batch | Fijo, 1 |
| Inmutable | Immutable | No aplica |
| División del tráfico | Traffic splitting | (no se usó) |

- Dejar **Tipo de actualización continua** en *Desactivado*: aplica a cambios de
  configuración, no a despliegues de código.
- Tomar captura de **Revisar cambios** y luego *Aplicar cambios*.
- Esperar a que el ambiente vuelva a **Ok** (~45 s) antes de desplegar: Beanstalk solo
  permite una operación a la vez. Este tiempo no cuenta en el de la estrategia.

### 3. Monitorear `/health` durante el despliegue

En PowerShell, cargar esta función una vez por ventana. Consulta `/health` cada segundo,
muestra versión y host, registra los errores en vez de detenerse, y guarda todo en
`health.log`:

```powershell
function Vigilar($carpeta, $url) {
  & { while ($true) {
      $t = Get-Date -Format "HH:mm:ss"
      try   { $r = Invoke-RestMethod "$url/health" -TimeoutSec 3; "$t  v$($r.version)  $($r.host)" }
      catch { "$t  ERROR  $($_.Exception.Message)" }
      Start-Sleep 1
  } } | Tee-Object -FilePath "$carpeta\health.log"
}
```

Uso (la carpeta debe existir; la URL va sin `/` al final; se detiene con **Ctrl+C**):

```powershell
Vigilar 2.2-rolling http://<url-del-ambiente>
```

Al terminar, contar los errores del log (0 = sin caída):

```powershell
(Select-String "ERROR" 2.2-rolling\health.log).Count
```

### 4. Desplegar y registrar

1. Arrancar el bucle **antes** de desplegar.
2. *Cargar e implementar* el `.zip` con una etiqueta descriptiva (`v1.0.2-rolling`, …).
3. Durante el despliegue revisar **Eventos**, **Estado y supervisión** e **Instancias (EC2)**,
   recargando para ver instancias nuevas o terminadas.
4. Al final: captura de Eventos con *Environment update completed successfully*, detener el
   bucle y contar errores.

## Hallazgos

- **All at once:** la más rápida, pero las 3 instancias reinician a la vez y el balanceador
  responde 502 mientras no queda ninguna sana. La consola lo registró (Warning por 4,3 % de
  respuestas 5xx).
- **Rolling:** sin caída, pero la capacidad baja a 2 de 3 instancias en cada lote. Cada lote
  tarda ~2,5 min; instalar el código toma ~35 s y el resto es la espera de los health checks
  del balanceador.
- **Rolling with additional batch:** nunca baja de 3 instancias (llega a 4). Solo hubo 3
  lotes: Beanstalk terminó la instancia original sobrante sin actualizarla. Un aviso
  *Degraded* transitorio aparece mientras la instancia terminada sigue registrada.
- **Immutable:** no toca las instancias en servicio; prueba la versión en una instancia,
  lanza el resto en un grupo de Auto Scaling temporal y luego las pasa al grupo principal.
  Llega a 6 instancias a la vez. La más segura y la más costosa.
- En todas salvo All at once **convivieron dos versiones** varios minutos: cada versión de la
  API y del esquema de base de datos debe ser compatible con la anterior.
- **Recomendación para producción:** Immutable.

## Cuidados

- **No capturar ni grabar** *Configuración → Propiedades del entorno*: muestra
  `RDS_PASSWORD` y `JWT_SECRET_KEY` en texto plano.
- El repositorio es público: no subir capturas de la consola, `health.log` ni `.env`.
- Immutable y el lote adicional crean instancias extra (costo). Hacer todo en una sesión y
  destruir el ambiente al terminar.
