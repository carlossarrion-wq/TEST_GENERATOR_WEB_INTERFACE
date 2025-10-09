# Plan de Pruebas Unitarias - Lambda Jira Integration

## 📋 Objetivo

Validar el correcto funcionamiento de la función Lambda de integración con Jira, asegurando que todos los componentes funcionen correctamente de forma aislada y en conjunto.

## 🎯 Alcance

### Componentes a Probar

1. **Services**
   - JiraClient: Cliente HTTP para comunicación con Jira API

2. **Handlers**
   - jiraImport: Importación de issues con filtros
   - getIssues: Obtención de issues específicos

3. **Utils**
   - validators: Validación de requests
   - jiraParser: Parsing y normalización de datos

4. **Integration**
   - index: Router principal y manejo de rutas

## 📊 Casos de Prueba

### 1. JiraClient Service

#### TC-001: Construcción del cliente
- **Descripción**: Verificar que el cliente se inicializa correctamente con credenciales válidas
- **Precondiciones**: Credenciales válidas disponibles
- **Pasos**:
  1. Crear instancia de JiraClient con credenciales
  2. Verificar que se configura baseURL correctamente
  3. Verificar que se configura autenticación
- **Resultado Esperado**: Cliente inicializado sin errores
- **Prioridad**: High

#### TC-002: Búsqueda de issues con JQL
- **Descripción**: Verificar búsqueda de issues usando JQL
- **Precondiciones**: Cliente inicializado, conexión a Jira disponible
- **Pasos**:
  1. Llamar searchIssues con JQL válido
  2. Verificar respuesta
- **Resultado Esperado**: Array de issues retornado
- **Prioridad**: High

#### TC-003: Construcción de JQL desde filtros
- **Descripción**: Verificar que buildJQL genera JQL correcto
- **Precondiciones**: Ninguna
- **Pasos**:
  1. Llamar buildJQL con filtros variados
  2. Verificar sintaxis JQL generada
- **Resultado Esperado**: JQL válido generado
- **Prioridad**: High
- **Datos de Prueba**:
  ```javascript
  {
    projectKey: "PDDSE2",
    issueTypes: ["Story", "Bug"],
    status: ["To Do"]
  }
  ```

#### TC-004: Manejo de errores 401
- **Descripción**: Verificar manejo de error de autenticación
- **Precondiciones**: Credenciales inválidas
- **Pasos**:
  1. Intentar búsqueda con credenciales incorrectas
  2. Capturar error
- **Resultado Esperado**: Error descriptivo "Authentication failed"
- **Prioridad**: High

#### TC-005: Retry en error 429
- **Descripción**: Verificar retry automático en rate limit
- **Precondiciones**: Mock de respuesta 429
- **Pasos**:
  1. Simular respuesta 429
  2. Verificar que se reintenta
- **Resultado Esperado**: 3 reintentos con backoff exponencial
- **Prioridad**: Medium

### 2. Validators Utils

#### TC-006: Validación de request de importación válido
- **Descripción**: Verificar validación exitosa de request correcto
- **Precondiciones**: Ninguna
- **Pasos**:
  1. Llamar validateJiraImportRequest con body válido
  2. Verificar resultado
- **Resultado Esperado**: `{valid: true, errors: []}`
- **Prioridad**: High

#### TC-007: Validación de request sin projectKey ni filters
- **Descripción**: Verificar rechazo de request inválido
- **Precondiciones**: Ninguna
- **Pasos**:
  1. Llamar validateJiraImportRequest con body vacío
  2. Verificar errores
- **Resultado Esperado**: `{valid: false, errors: [...]}`
- **Prioridad**: High

#### TC-008: Validación de maxResults fuera de rango
- **Descripción**: Verificar validación de límites
- **Precondiciones**: Ninguna
- **Pasos**:
  1. Llamar con maxResults = 150
  2. Verificar error
- **Resultado Esperado**: Error "maxResults must be between 1 and 100"
- **Prioridad**: Medium

#### TC-009: Validación de issueKeys request
- **Descripción**: Verificar validación de array de keys
- **Precondiciones**: Ninguna
- **Pasos**:
  1. Llamar validateIssueKeysRequest con array válido
  2. Verificar resultado
- **Resultado Esperado**: `{valid: true, errors: []}`
- **Prioridad**: High

#### TC-010: Validación de issueKeys vacío
- **Descripción**: Verificar rechazo de array vacío
- **Precondiciones**: Ninguna
- **Pasos**:
  1. Llamar con issueKeys = []
  2. Verificar error
- **Resultado Esperado**: Error "issueKeys array cannot be empty"
- **Prioridad**: Medium

### 3. JiraParser Utils

#### TC-011: Parsing de issue válido
- **Descripción**: Verificar normalización de issue de Jira
- **Precondiciones**: Issue raw de Jira disponible
- **Pasos**:
  1. Llamar parseIssue con issue raw
  2. Verificar estructura normalizada
- **Resultado Esperado**: Objeto con campos: id, key, summary, description, etc.
- **Prioridad**: High

#### TC-012: Parsing de issue sin campos opcionales
- **Descripción**: Verificar manejo de campos faltantes
- **Precondiciones**: Issue con campos mínimos
- **Pasos**:
  1. Llamar parseIssue con issue incompleto
  2. Verificar valores por defecto
- **Resultado Esperado**: Campos opcionales con valores por defecto
- **Prioridad**: Medium

#### TC-013: Extracción de custom fields
- **Descripción**: Verificar extracción de campos personalizados
- **Precondiciones**: Issue con customfields
- **Pasos**:
  1. Llamar extractCustomFields
  2. Verificar mapeo
- **Resultado Esperado**: Custom fields mapeados correctamente
- **Prioridad**: Medium

#### TC-014: Cálculo de estadísticas
- **Descripción**: Verificar cálculo de stats de issues
- **Precondiciones**: Array de issues
- **Pasos**:
  1. Llamar calculateStatistics con 10 issues
  2. Verificar contadores
- **Resultado Esperado**: Stats correctas por status, priority, type
- **Prioridad**: Medium

### 4. JiraImport Handler

#### TC-015: Importación exitosa con projectKey
- **Descripción**: Verificar importación básica por proyecto
- **Precondiciones**: Credenciales válidas, proyecto existe
- **Pasos**:
  1. Invocar handler con projectKey="PDDSE2"
  2. Verificar respuesta
- **Resultado Esperado**: Status 200, issues array, pagination, statistics
- **Prioridad**: High

#### TC-016: Importación con filtros múltiples
- **Descripción**: Verificar filtrado avanzado
- **Precondiciones**: Credenciales válidas
- **Pasos**:
  1. Invocar con projectKey + filters
  2. Verificar JQL generado
  3. Verificar resultados filtrados
- **Resultado Esperado**: Solo issues que cumplen filtros
- **Prioridad**: High

#### TC-017: Importación con JQL personalizado
- **Descripción**: Verificar uso de JQL directo
- **Precondiciones**: Credenciales válidas
- **Pasos**:
  1. Invocar con jql custom
  2. Verificar que se usa el JQL proporcionado
- **Resultado Esperado**: Búsqueda con JQL custom
- **Prioridad**: Medium

#### TC-018: Error de validación en request
- **Descripción**: Verificar respuesta a request inválido
- **Precondiciones**: Ninguna
- **Pasos**:
  1. Invocar sin projectKey ni filters
  2. Verificar respuesta de error
- **Resultado Esperado**: Status 400, error de validación
- **Prioridad**: High

#### TC-019: Error de autenticación
- **Descripción**: Verificar manejo de credenciales inválidas
- **Precondiciones**: Credenciales incorrectas
- **Pasos**:
  1. Invocar con credenciales malas
  2. Verificar error
- **Resultado Esperado**: Status 401, mensaje descriptivo
- **Prioridad**: High

### 5. GetIssues Handler

#### TC-020: Obtención exitosa de issues
- **Descripción**: Verificar obtención de issues por keys
- **Precondiciones**: Issues existen en Jira
- **Pasos**:
  1. Invocar con array de keys válidos
  2. Verificar respuesta
- **Resultado Esperado**: Status 200, issues encontrados
- **Prioridad**: High

#### TC-021: Detección de issues faltantes
- **Descripción**: Verificar identificación de keys no encontrados
- **Precondiciones**: Algunos keys no existen
- **Pasos**:
  1. Invocar con mix de keys válidos e inválidos
  2. Verificar summary
- **Resultado Esperado**: missingKeys array con keys no encontrados
- **Prioridad**: Medium

#### TC-022: Error con array vacío
- **Descripción**: Verificar validación de array vacío
- **Precondiciones**: Ninguna
- **Pasos**:
  1. Invocar con issueKeys = []
  2. Verificar error
- **Resultado Esperado**: Status 400, error de validación
- **Prioridad**: Medium

### 6. Index Router

#### TC-023: Routing a /jira/import
- **Descripción**: Verificar enrutamiento correcto
- **Precondiciones**: Ninguna
- **Pasos**:
  1. Invocar con path="/jira/import"
  2. Verificar que llama a jiraImport handler
- **Resultado Esperado**: Request enrutado correctamente
- **Prioridad**: High

#### TC-024: Routing a /jira/issues
- **Descripción**: Verificar enrutamiento correcto
- **Precondiciones**: Ninguna
- **Pasos**:
  1. Invocar con path="/jira/issues"
  2. Verificar que llama a getIssues handler
- **Resultado Esperado**: Request enrutado correctamente
- **Prioridad**: High

#### TC-025: Manejo de OPTIONS (CORS)
- **Descripción**: Verificar respuesta a preflight
- **Precondiciones**: Ninguna
- **Pasos**:
  1. Invocar con httpMethod="OPTIONS"
  2. Verificar headers CORS
- **Resultado Esperado**: Status 200, headers CORS correctos
- **Prioridad**: Medium

#### TC-026: Path no encontrado
- **Descripción**: Verificar respuesta 404
- **Precondiciones**: Ninguna
- **Pasos**:
  1. Invocar con path desconocido
  2. Verificar respuesta
- **Resultado Esperado**: Status 404, lista de endpoints disponibles
- **Prioridad**: Low

## 🔧 Configuración de Tests

### Herramientas
- **Framework**: Jest
- **Mocking**: Jest mocks para axios
- **Coverage**: Jest coverage reporter

### Estructura de Archivos
```
tests/
├── unit/
│   ├── services/
│   │   └── jiraClient.test.js
│   ├── handlers/
│   │   ├── jiraImport.test.js
│   │   └── getIssues.test.js
│   ├── utils/
│   │   ├── validators.test.js
│   │   └── jiraParser.test.js
│   └── index.test.js
└── fixtures/
    ├── jiraIssues.json
    └── jiraResponses.json
```

## 📈 Métricas de Éxito

### Cobertura de Código
- **Objetivo**: ≥ 80% de cobertura
- **Líneas**: ≥ 80%
- **Funciones**: ≥ 85%
- **Branches**: ≥ 75%

### Criterios de Aceptación
- ✅ Todos los tests pasan
- ✅ No hay errores de linting
- ✅ Cobertura ≥ 80%
- ✅ Tiempo de ejecución < 30 segundos
- ✅ Sin warnings de deprecación

## 🚀 Ejecución

### Comandos
```bash
# Ejecutar todos los tests
npm test

# Tests con coverage
npm run test:coverage

# Tests en modo watch
npm run test:watch

# Test específico
npm test -- jiraClient.test.js
```

## 📝 Priorización

### Alta Prioridad (Must Have)
- TC-001, TC-002, TC-003, TC-006, TC-007, TC-009, TC-011, TC-015, TC-016, TC-018, TC-019, TC-020, TC-023, TC-024

### Media Prioridad (Should Have)
- TC-004, TC-005, TC-008, TC-010, TC-012, TC-013, TC-014, TC-017, TC-021, TC-022, TC-025

### Baja Prioridad (Nice to Have)
- TC-026

## 📊 Resumen

- **Total de Casos**: 26
- **Alta Prioridad**: 14 (54%)
- **Media Prioridad**: 11 (42%)
- **Baja Prioridad**: 1 (4%)

## 🎯 Próximos Pasos

1. Implementar tests de alta prioridad
2. Configurar Jest y coverage
3. Crear fixtures de datos de prueba
4. Ejecutar y validar cobertura
5. Implementar tests de media prioridad
6. Documentar resultados
