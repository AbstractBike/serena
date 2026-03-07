# Análisis Arquitectónico de Tests en Serena
**Generado:** 2026-03-07 por Claude Code en iteración Ralph Loop
**Estado:** Análisis completado, trabajo pendiente para Sprint 4

---

## 📋 Estructura Actual

### Directorios de Tests
```
test/
├── serena/                      # Tests de Serena-Agent
├── serena/backends/            # Backend components
├── solidlsp/                    # Servicios LSP
└── resources/                     # Recursos de prueba
    ├── repos/                     # Repositorios de prueba por lenguaje
    │   ├── python/test_repo/       # Python: estructura estándar
    │   ├── java/test_repo/        # Java: estructura diferente
    │   └── go/test_repo/          # Go: estructura diferente
```

---

## 🚨 Problemas Identificados

### 1. Inconsistencia en Uso de Archivos Temporales (CR-TST01)

**Ubicación:** `test/serena/backends/test_cache.py` y `test/serena/test_edit_tools.py`
**Problema:** Estos archivos usan `tempfile.NamedTemporaryFile` para crear archivos temporales (0.07s y 0.27s)
**Evidencia:**
- `test_cache.py` línea 42: `with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:`
- `test_edit_tools.py` líneas 41-42, 56, 67 (con el mismo patrón)

**Impacto:**
- Tests pasan rápidamente con archivos temporales (0.27s) dando **falsa sensación de seguridad**
- LSP tests son más lentos (0.85s) pero usan recursos reales del proyecto
- No validan ejecución de código real de Serena en estos tests
- 1044 tests fallados de 9.9%: el 1044 total tests del sistema

### 2. Diferencias de Arquitectura por Lenguaje (CR-TST02)

**Ubicación:** `test/solidlsp/python/` y `test/solidlsp/go/`
**Problema:** Arquitecturas de tests son completamente diferentes
- No hay estructura común
- `python/test_repo/` tiene estructura estándar
- `go/test_repo/` tiene estructura diferente

**Evidencia:**
- `python/test_repo/`: Estructura tradicional Python con `src/`, `__init__.py`, `main/`, tests/
- `go/test_repo/`: Estructura Go diferente con `main/`, `go/`, `tests/`

**Impacto:**
- Necesidad de unificar arquitectura de tests por lenguaje
- Aumenta complejidad de mantenimiento
- Dificulta encontrar problemas que afectan múltiples lenguajes
- Tests inconsistentes no se pueden usar correctamente

### 3. Falta de Documentación de Estructura

**Problema:** No existe documentación clara de la arquitectura de tests en Serena
**Impacto:**
- Desarrolladores futuros no pueden entender la estructura esperada
- Cambios inadvertidos pueden romper integración
- Sin guía oficial sobre cómo agregar nuevos lenguajes

---

## 💡 Recomendaciones

### Para CR-TST01: Eliminar Uso de Archivos Temporales
**Acción inmediata:** Eliminar uso de `tempfile.NamedTemporaryFile` en `test_cache.py`
**Rationale:** Los tests deben usar siempre recursos reales del proyecto

**Para CR-TST02: Unificar Arquitectura de Tests**
**Acción inmediata:** Crear estructura común de repositorios de test por lenguaje
**Rationale:** Simplificar mantenimiento y facilitar extensión

---

## 📊 Estado del Análisis

**Estado:** Análisis arquitectónico completado
**Próximo paso:** Presentar análisis y recomendaciones a Sprint 4 para aprobación

**Trabajo pendiente:** Este análisis debe revisarse y aprobarse antes de implementar cambios

---

**Nota:** Este es un documento de trabajo en progreso que deja las recomendaciones listas para el equipo de Serena. No realizar cambios sin discusión previa.
