# Evaluación de Accuracy del Agente

Este directorio contiene el sistema de evaluación para medir el accuracy del agente de actuadores.

## Archivos

- `dataset.json`: Dataset con 20 casos de prueba
- `results/`: Directorio con resultados de evaluaciones pasadas

## Casos de prueba (20 total)

### Por categoría:
- **exact_search** (4 casos): Búsquedas por part number exacto
- **semantic_search** (12 casos): Búsquedas semánticas con diferentes requisitos
- **incomplete_spec** (2 casos): Especificaciones incompletas que requieren clarificación
- **context_memory** (2 casos): Tests de memoria contextual

## Ejecutar evaluación

### Opción 1: Dentro del contenedor Docker

```bash
docker-compose exec backend python evaluate_agent.py
```

### Opción 2: Localmente

```bash
cd backend
python evaluate_agent.py
```

## Métricas evaluadas

Para cada caso de prueba se evalúa:

1. **tool_usage_correct**: ¿Se usó la herramienta correcta?
2. **expected_fields_present**: ¿Están los campos esperados? (80% threshold)
3. **part_number_correct**: ¿El part number es correcto?
4. **context_type_correct**: ¿El voltage/power type es correcto?
5. **min_results_satisfied**: ¿Se devolvieron suficientes resultados?
6. **clarification_asked**: ¿Se pidió clarificación cuando era necesario?
7. **ground_truth**: ¿Los valores numéricos coinciden con ground truth? (tolerancia 5%)

### Ground Truth Validation

Para casos con `ground_truth` definido, se valida:
- Valores numéricos exactos (torque, potencia, velocidad, etc.)
- Tolerancia de ±5% para valores numéricos
- Valores de texto exactos (context_type, part number)
- Score general de precisión de datos (0-100%)

## Scoring

- **Score individual**: 0-100% basado en métricas pasadas
- **Accuracy general**: % de tests que pasaron todos los checks
- **Score promedio**: Promedio de scores individuales

## Integración con Langfuse

El script de evaluación está completamente integrado con Langfuse y utiliza sus herramientas nativas:

### Dataset en Langfuse

El script automáticamente:
1. **Crea un dataset** llamado `actuator-agent-eval` en Langfuse (o lo actualiza si ya existe)
2. **Agrega todos los casos de prueba** como items del dataset con:
   - Input: query del usuario, categoría, herramienta esperada
   - Expected Output: ground truth, part numbers esperados, context types, etc.
   - Metadata: categoría y descripción del test

Puedes ver y gestionar el dataset en el dashboard de Langfuse:
- Navega a **Datasets** en el menú
- Busca `actuator-agent-eval`
- Verás todos los casos de prueba con sus inputs y expected outputs

### Traces y Scores

Cada ejecución del agente durante la evaluación:
- Se registra automáticamente como una **trace** (gracias al `CallbackHandler` en el agente)
- Recibe múltiples **scores**:
  - `tool_usage_correct`: 1.0 si se usó la herramienta correcta, 0.0 si no
  - `expected_fields_present`: 1.0 si los campos esperados están presentes
  - `part_number_correct`: 1.0 si el part number es correcto
  - `context_type_correct`: 1.0 si el context type es correcto
  - `min_results_satisfied`: 1.0 si se devolvieron suficientes resultados
  - `clarification_asked`: 1.0 si se pidió clarificación cuando era necesario
  - `ground_truth_accuracy`: Accuracy del ground truth (0.0-1.0)
  - `overall_score`: Score general del test (0.0-1.0)

### Visualización en Langfuse

Después de ejecutar el script, visita tu dashboard de Langfuse para ver:

1. **Traces**: Cada ejecución del agente durante la evaluación
   - Filtra por `test_case_id` en metadata para encontrar casos específicos
   - Revisa los inputs, outputs y tool calls

2. **Scores**: Métricas de evaluación adjuntas a cada trace
   - Ve el rendimiento del agente en cada métrica
   - Identifica qué tests están fallando y por qué

3. **Datasets**: El dataset `actuator-agent-eval` con todos los casos de prueba
   - Gestiona tus casos de prueba desde la UI
   - Ejecuta evaluaciones directamente desde Langfuse (si está disponible en tu plan)

4. **Analytics**: Métricas agregadas
   - Accuracy por categoría
   - Tendencias a lo largo del tiempo
   - Comparación entre diferentes versiones del agente

### Acceso al Dashboard

1. Ve a https://cloud.langfuse.com (o tu instancia local)
2. Abre tu proyecto
3. Navega a:
   - **Datasets** → `actuator-agent-eval` para ver los casos de prueba
   - **Traces** → Filtra por metadata `test_case_id` para ver ejecuciones específicas
   - **Scores** → Ve todas las métricas de evaluación

## Resultados

Los resultados se guardan en:
- `evaluation/results/{run_name}.json`: Resultados completos
- `evaluation/results/latest.json`: Última evaluación

## Interpretar resultados

### Accuracy objetivo
- **≥ 90%**: Excelente
- **80-89%**: Bueno
- **70-79%**: Aceptable, requiere mejoras
- **< 70%**: Requiere optimización urgente

### Categorías más comunes de fallos
1. Herramienta incorrecta usada
2. Campos faltantes en respuesta
3. No pide clarificación cuando debería
4. Resultados insuficientes

## Agregar nuevos casos

### Ejemplo con ground_truth (recomendado para exact_search):

```json
{
  "id": "test_XXX",
  "category": "exact_search",
  "input": "I need actuator 763A00-11330C00/A",
  "expected_tool": "search_by_part_number",
  "expected_part_number": "763A00-11330C00/A",
  "ground_truth": {
    "base_part_number": "763A00-11330C00/A",
    "context_type": "220V 3 Phase Power",
    "output_torque_nm": 300.0,
    "duty_cycle_54pct": 70.0,
    "motor_power_watts": 40.0,
    "operating_speed_sec_60_hz": 26.0,
    "cycles_per_hour_cycles": 39.0,
    "starts_per_hour_starts": 1200.0
  },
  "description": "Exact part number search with full spec verification"
}
```

### Ejemplo sin ground_truth (para semantic_search):

```json
{
  "id": "test_XXX",
  "category": "semantic_search",
  "input": "I need high torque actuator",
  "expected_tool": "semantic_search",
  "min_results": 3,
  "validate_high_torque": true,
  "description": "Vague query - high torque"
}
```

### Campos disponibles:

- `id`: Identificador único (requerido)
- `category`: exact_search|semantic_search|incomplete_spec|context_memory (requerido)
- `input`: Mensaje del usuario (requerido)
- `expected_tool`: Herramienta esperada (opcional)
- `expected_part_number`: Part number esperado (opcional)
- `expected_context_type_contains`: Texto esperado en context_type (opcional)
- `ground_truth`: Valores exactos esperados (opcional, recomendado para exact_search)
- `min_results`: Mínimo de resultados (opcional)
- `max_results`: Máximo de resultados (opcional)
- `should_ask_clarification`: Si debe pedir clarificación (opcional)
- `validate_*`: Validaciones especiales (opcional)
- `description`: Descripción del test (requerido)

## Ejemplo de salida

```
RESUMEN DE EVALUACIÓN
================================================================================

Total de tests: 20
Pasados: 18 (90.0%)
Fallidos: 2
Score promedio: 92.5%

ACCURACY POR CATEGORÍA
--------------------------------------------------------------------------------
exact_search          4/ 4 (100.0%)
semantic_search      11/12 (91.7%)
incomplete_spec       2/ 2 (100.0%)
context_memory        1/ 2 (50.0%)

TESTS FALLIDOS
--------------------------------------------------------------------------------
test_016: context_memory
   Input: single phase
   Failed: context_type_correct
```

