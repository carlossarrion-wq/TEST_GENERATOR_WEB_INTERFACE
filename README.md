# Test Plan Generator - Web Interface

## 📋 Descripción General

Aplicación web para la generación automática de planes de pruebas a partir de requerimientos funcionales, utilizando inteligencia artificial. La interfaz permite crear, refinar, guardar y exportar planes de pruebas de manera intuitiva y eficiente.

## ✨ Características Principales

### 1. **Formulario de Entrada de Información**
- **Título del Plan**: Campo de texto para identificar el plan de pruebas
- **ID del Plan**: Identificador único del plan
- **Referencia**: Campo opcional para referencias externas (ej: tickets de Jira)
- **Requerimientos Funcionales**: Área de texto para describir los requisitos que debe cubrir el plan
- **Tipos de Prueba**: Selección múltiple mediante tarjetas visuales:
  - Pruebas Unitarias
  - Pruebas de Sistema
  - Pruebas de Integración
  - Pruebas de Performance
  - Pruebas de Regresión
- **Porcentaje de Cobertura**: Control deslizante segmentado (10%-100%, valor por defecto: 80%)
- **Rango de Casos de Prueba**: Control dual para definir mínimo y máximo de casos (1-50)

### 2. **Generación de Casos de Prueba**
El botón "Generate Test Plan" invoca un agente de IA que genera casos de prueba con la siguiente estructura:

**Campos de cada Caso de Prueba:**
- Identificador del Caso
- Nombre del Caso
- Descripción
- Prioridad (High, Medium, Low)
- Precondiciones
- Pasos de Prueba (con número de secuencia y descripción)
- Resultado Esperado
- Datos de Prueba necesarios

**Comportamiento del Botón:**
- Solo está habilitado cuando no hay casos de prueba generados
- Se deshabilita automáticamente después de generar un plan
- Permite generar un nuevo plan solo después de eliminar todos los casos existentes

### 3. **Visualización de Casos de Prueba**
- **Tabla HTML Interactiva**: Muestra todos los casos generados con columnas:
  - ID
  - Nombre
  - Descripción
  - Prioridad (con badges de colores)
  - Acciones (Ver detalles y Eliminar)
- **Modal de Detalles**: Al hacer clic en "View Details", se abre una ventana modal flotante que muestra:
  - Información completa del caso
  - Pasos de prueba numerados
  - Precondiciones
  - Resultado esperado
  - Datos de prueba necesarios
- **Botón "Delete All"**: Permite eliminar todos los casos de prueba con confirmación previa

### 4. **Chat de Refinamiento**
- **Interfaz de Chat Interactiva**: Permite comunicación bidireccional con el agente de IA
- **Funcionalidades**:
  - Solicitar modificaciones específicas al plan
  - Añadir casos de prueba para casuísticas particulares
  - Ajustar prioridades o detalles de casos existentes
  - Regenerar casos específicos
- **Botón "Clear Chat"**: Reinicia la conversación manteniendo solo el mensaje inicial del asistente
- **Historial Persistente**: Las conversaciones se mantienen durante la sesión

### 5. **Gestión de Planes**

#### **Guardar Plan**
- Almacena el plan completo en LocalStorage
- Incluye: título, ID, referencia, requerimientos, tipos de prueba, cobertura, rango de casos y todos los casos generados
- Permite recuperar el trabajo posteriormente

#### **Cargar Plan**
- Modal con lista de planes guardados
- Muestra: título, ID, referencia, fecha de guardado y número de casos
- Permite seleccionar y cargar cualquier plan guardado
- Opción para eliminar planes guardados

#### **Importar desde Jira**
- Funcionalidad para importar información desde tickets de Jira
- Integración con sistemas externos de gestión de proyectos

#### **Exportar Plan**
Tres formatos de exportación disponibles:
- **CSV**: Formato tabular para análisis en hojas de cálculo
- **JSON**: Formato estructurado para integración con otras herramientas
- **BDD (Gherkin)**: Formato Given-When-Then para pruebas de comportamiento

#### **Nuevo Plan**
- Limpia todos los campos y casos de prueba
- Solicita confirmación antes de descartar el trabajo actual
- Reinicia el estado de la aplicación

### 6. **Sistema de Autenticación**
- **Página de Login**: Interfaz de inicio de sesión con validación
- **Gestión de Sesión**: Control de acceso mediante SessionStorage
- **Redirección Automática**: Protección de rutas no autenticadas

## 🎨 Diseño y Estilo

### **Look & Feel**
- Basado en el dashboard de AWS Bedrock Usage Control
- **Paleta de Colores**:
  - Color principal: Teal (#319795)
  - Segmentos activos: #BED9DA
  - Fondo: Gradiente oscuro (#0f172a a #1e293b)
- **Tipografía**: Amazon Ember (con fallback a system fonts)
- **Efectos Visuales**:
  - Glassmorphism con backdrop-filter
  - Sombras suaves y bordes redondeados
  - Transiciones fluidas en interacciones

### **Componentes Personalizados**
- Controles deslizantes segmentados con indicadores visuales
- Tarjetas de selección de tipo de prueba con iconos
- Badges de prioridad con colores distintivos
- Modales con diseño glassmorphic
- Botones con estados hover y disabled

## 🛠️ Tecnologías Utilizadas

- **HTML5**: Estructura semántica
- **CSS3**: Estilos avanzados con variables CSS, flexbox y grid
- **JavaScript (ES6+)**: Lógica de aplicación vanilla (sin frameworks)
- **LocalStorage**: Persistencia de datos local
- **SessionStorage**: Gestión de sesión de usuario

## 📁 Estructura de Archivos

```
TEST_GENERATOR_WEB_INTERFACE/
├── index.html              # Página principal de la aplicación
├── login.html              # Página de autenticación
├── README.md               # Este archivo
├── css/
│   └── styles.css          # Estilos globales de la aplicación
└── js/
    └── app.js              # Lógica de la aplicación
```

## 🚀 Cómo Usar

1. **Iniciar Sesión**: Acceder a través de `login.html`
2. **Crear Plan**: Completar el formulario con la información del plan
3. **Seleccionar Tipos de Prueba**: Hacer clic en las tarjetas de tipos deseados
4. **Ajustar Parámetros**: Configurar cobertura y rango de casos con los sliders
5. **Generar**: Hacer clic en "Generate Test Plan"
6. **Revisar**: Examinar los casos generados en la tabla
7. **Refinar**: Usar el chat para solicitar ajustes al agente de IA
8. **Gestionar**: Guardar, exportar o crear un nuevo plan según necesidad

## 📊 Flujo de Trabajo

```
Login → Formulario → Generación IA → Visualización → Refinamiento → Exportación/Guardado
```

## 🔒 Seguridad

- Autenticación requerida para acceso
- Validación de sesión en cada carga de página
- Almacenamiento local seguro de datos

## 🎯 Casos de Uso

1. **QA Engineer**: Crear planes de pruebas completos para nuevas funcionalidades
2. **Test Manager**: Generar y exportar planes para distribución al equipo
3. **Developer**: Crear casos de prueba unitarios y de integración
4. **Product Owner**: Validar cobertura de requerimientos funcionales

## 📝 Notas Técnicas

- Los casos de prueba se almacenan en un array global `testCases`
- La persistencia se maneja mediante LocalStorage con clave `savedTestPlans`
- Los sliders utilizan segmentos activos para mejor visualización
- El estado de los botones se actualiza dinámicamente según el contenido

## 🔄 Actualizaciones Futuras

- Integración real con AWS Lambda para generación de IA
- Conexión con API de Jira para importación automática
- Exportación a formatos adicionales (Excel, PDF)
- Colaboración en tiempo real entre usuarios
- Historial de versiones de planes

---

**Versión**: 1.0.0  
**Última Actualización**: Enero 2025  
**Desarrollado con**: HTML5, CSS3, JavaScript ES6+
