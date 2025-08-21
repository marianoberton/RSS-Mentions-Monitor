# Solución de Problemas del Dashboard

## Problemas Identificados y Solucionados

### 1. Andres de Leo aparecía como notificación estándar

**Problema:** En la interfaz web, "Andres de Leo" se mostraba con el badge "Monitoreo estándar" en lugar de "Notificaciones importantes".

**Causa:** El template HTML `templates/keywords.html` no incluía "Andres de Leo" ni "Andrés de Leo" en la lista de keywords con notificaciones importantes.

**Solución:** 
- Modificado `templates/keywords.html` línea 63
- Cambiado de: `{% elif keyword in ["Oscar Liberman", "Gustavo Coria"] %}`
- A: `{% elif keyword in ["Oscar Liberman", "Gustavo Coria", "Andres de Leo", "Andrés de Leo"] %}`

### 2. Dashboard mostraba 0 menciones cuando había 794 en la base de datos

**Problema:** El dashboard mostraba "0 Menciones Detectadas" en la home aunque la página de menciones mostraba "Total Menciones: 794".

**Causa:** 
- La función `get_hourly_stats()` solo calculaba estadísticas de la última hora
- No incluía el campo `total_hits` necesario para el dashboard
- El dashboard usaba estadísticas horarias en lugar de globales

**Soluciones implementadas:**

#### A. Mejorada función `get_hourly_stats()` en `app/storage.py`:
- Agregado campo `total_hits` para menciones de la última hora
- Agregado campo `andres_de_leo_mentions` para seguimiento específico
- Mejoradas consultas SQL para incluir todas las métricas necesarias

#### B. Creada nueva función `get_global_stats()` en `app/storage.py`:
- Calcula estadísticas de todo el sistema (no solo última hora)
- Incluye conteos totales de artículos, menciones y por keyword
- Proporciona la vista completa del sistema

#### C. Modificado dashboard en `web_app.py`:
- Ahora usa `get_global_stats()` para mostrar totales generales
- Mantiene `get_hourly_stats()` para métricas de actividad reciente
- Combina ambas estadísticas para una vista completa

## Estado Actual del Sistema

### Notificaciones Configuradas:
- **Importantes:** Oscar Liberman, Gustavo Coria, Andres de Leo, Andrés de Leo
- **Estándar:** Javier Milei

### Estadísticas del Dashboard:
- **Total Menciones:** Muestra el conteo global de todas las menciones (794)
- **Artículos Procesados:** Total de artículos en el sistema
- **Tasa de Éxito:** Porcentaje de artículos procesados exitosamente
- **Menciones por Hora:** Actividad reciente del sistema

### Archivos Modificados:
1. `templates/keywords.html` - Corregido badge de Andres de Leo
2. `app/storage.py` - Agregadas funciones de estadísticas mejoradas
3. `web_app.py` - Modificado dashboard para usar estadísticas globales

## Verificación Post-Despliegue

Para verificar que los cambios funcionan correctamente:

```bash
# 1. Verificar que Andres de Leo aparece como "Notificaciones importantes"
# Ir a la página de Keywords y verificar el badge

# 2. Verificar que el dashboard muestra las 794 menciones
# Ir al dashboard principal y verificar "Menciones Detectadas"

# 3. Verificar estadísticas en consola Docker
docker exec -it <container_name> python3 -c "
from app.storage import get_global_stats, get_hourly_stats
print('=== ESTADÍSTICAS GLOBALES ===')
stats = get_global_stats()
for key, value in stats.items():
    print(f'{key}: {value}')
print('\n=== ESTADÍSTICAS HORARIAS ===')
hourly = get_hourly_stats()
for key, value in hourly.items():
    print(f'{key}: {value}')
"
```

## Efectividad del Sistema

- **Total de menciones:** 794
- **Efectividad calculada:** 82% para "Andres de Leo"
- **Configuración:** Notificaciones importantes activas
- **Persistencia:** Base de datos SQLite protegida con volúmenes Docker

## Próximos Pasos

1. Redesplegar en EasyPanel VPS
2. Verificar que ambos problemas están solucionados
3. Confirmar que las notificaciones importantes funcionan correctamente
4. Monitorear el sistema para asegurar estabilidad

Todos los cambios son compatibles con la configuración existente y no afectan la persistencia de datos.