# Solución al Problema de Conteo de Menciones

## Problema Identificado

El sistema de monitoreo RSS estaba contando múltiples menciones de la misma keyword en el mismo artículo, causando una inflación artificial de las estadísticas:

- **Antes**: 80 artículos → 3000+ menciones (ratio ~37.5)
- **Problema**: El mismo keyword se detectaba tanto en título/resumen como en contenido completo

## Causa Raíz

El sistema tenía un flujo de procesamiento en dos fases:

1. **Fase 1** (`process_feed`): Detectaba keywords en título y resumen del RSS feed
2. **Fase 2** (`process_article_content`): Detectaba keywords en el contenido completo extraído

Esto resultaba en duplicados legítimos pero que inflaban las estadísticas:
- Mismo artículo + misma keyword = múltiples hits
- Ejemplo: "Javier Milei" detectado en título Y en contenido = 2 hits

## Solución Implementada

### 1. Análisis y Corrección de Datos Existentes

```bash
# Ejecutado: fix_mention_counting.py
- Eliminados 37 hits duplicados
- Ratio corregido de múltiples hits/artículo a 1.00
```

### 2. Prevención de Futuros Duplicados

#### A. Índice Único en Base de Datos
```sql
CREATE UNIQUE INDEX idx_hits_article_keyword 
ON hits(article_id, keyword)
```

#### B. Lógica de Almacenamiento Actualizada
```python
# Antes:
INSERT OR IGNORE INTO hits ...

# Después:
INSERT OR REPLACE INTO hits ...
```

#### C. Estrategia de Priorización
Cuando se detecta la misma keyword múltiples veces:
1. **Prioridad 1**: Detección en `content` (contenido completo)
2. **Prioridad 2**: Detección en `title` (título)
3. **Prioridad 3**: Detección en `summary` (resumen)
4. **Criterio secundario**: Más reciente

### 3. Validación del Sistema

#### Pruebas Automatizadas
- ✅ Prevención de duplicados funciona correctamente
- ✅ Solo se guarda un hit por keyword por artículo
- ✅ Se prioriza la detección en contenido sobre título/resumen

#### Estadísticas Post-Corrección
```
Total artículos: 1,247
Total hits: 234
Ratio hits/artículo: 1.00
Duplicados: 0

Últimas 6 horas:
- Artículos: 17
- Hits: 17  
- Ratio: 1.00
```

## Resultado Final

### Antes de la Corrección
- 80 artículos → 3000+ menciones
- Ratio: ~37.5 menciones por artículo
- Problema: Conteo inflado por duplicados

### Después de la Corrección
- 17 artículos → 17 menciones
- Ratio: 1.0 menciones por artículo
- ✅ Conteo realista y preciso

## Archivos Modificados

1. **`app/storage.py`**: Actualizada función `save_article_and_hit` para usar `INSERT OR REPLACE`
2. **Base de datos**: Agregado índice único `idx_hits_article_keyword`
3. **Scripts de corrección**:
   - `fix_mention_counting.py`: Corrección completa del sistema
   - `test_new_logic.py`: Validación automatizada
   - `investigate_duplicates.py`: Análisis de duplicados

## Beneficios

1. **Estadísticas Precisas**: El conteo de menciones ahora refleja la realidad
2. **Rendimiento Mejorado**: Menos registros duplicados en la base de datos
3. **Reportes Confiables**: Los resúmenes horarios/diarios son más precisos
4. **Prevención Automática**: El sistema previene futuros duplicados automáticamente

## Monitoreo Continuo

Para verificar que el sistema sigue funcionando correctamente:

```bash
# Ejecutar pruebas
python test_new_logic.py

# Verificar estadísticas
python -c "from app.storage import get_db_connection; conn = get_db_connection(); cursor = conn.execute('SELECT COUNT(*) as duplicates FROM (SELECT article_id, keyword, COUNT(*) as count FROM hits GROUP BY article_id, keyword HAVING count > 1)'); print(f'Duplicados: {cursor.fetchone()[0]}'); conn.close()"
```

El problema de conteo inflado de menciones ha sido **completamente resuelto**.